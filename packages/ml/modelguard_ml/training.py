"""Reproducible training + holdout evaluation for the baseline and champion PD models.

One scikit-learn Pipeline carries preprocessing and the estimator so the same object is used
for training, validation and monitoring scoring (no train/serve skew). Everything needed to
reproduce a run (seed, features, hyperparameters, package versions, data checksum) is captured
in `TrainingResult.config`.
"""

from __future__ import annotations

import importlib.metadata as md
import json
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from modelguard_ml import metrics as M
from modelguard_ml.drift import numeric_bins, open_edges
from modelguard_ml.fairness import group_metrics
from modelguard_ml.spec import SYNTHETIC_SPEC, FeatureSpec
from modelguard_ml.splits import SplitResult, choose_split
from modelguard_ml.stats_tests import two_sample_ks

MODEL_TYPES = ("baseline", "champion")
DEFAULT_HYPERPARAMS: dict[str, dict[str, Any]] = {
    "baseline": {"C": 1.0, "max_iter": 2000, "class_weight": None},
    "champion": {
        "learning_rate": 0.04,
        "max_iter": 150,
        "max_depth": 3,
        "max_leaf_nodes": 8,
        "min_samples_leaf": 60,
        "l2_regularization": 5.0,
        "early_stopping": False,
    },
}


def package_versions() -> dict[str, str]:
    out = {"python": platform.python_version()}
    for name in ("numpy", "pandas", "scikit-learn", "scipy", "joblib"):
        try:
            out[name] = md.version(name)
        except md.PackageNotFoundError:
            out[name] = "unknown"
    return out


def build_preprocessor(spec: FeatureSpec = SYNTHETIC_SPEC) -> ColumnTransformer:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    transformers: list[tuple[str, Any, list[str]]] = [("num", numeric, list(spec.numeric))]
    if spec.categorical:
        categorical = Pipeline(
            [
                ("impute", SimpleImputer(strategy="most_frequent")),
                (
                    "onehot",
                    OneHotEncoder(
                        categories=[list(levels) for levels in spec.categorical.values()],
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),
                ),
            ]
        )
        transformers.append(("cat", categorical, list(spec.categorical)))
    return ColumnTransformer(transformers)


def build_pipeline(
    model_type: str, seed: int, hyperparams: dict[str, Any] | None = None, spec: FeatureSpec = SYNTHETIC_SPEC
) -> Pipeline:
    hp = {**DEFAULT_HYPERPARAMS[model_type], **(hyperparams or {})}
    if model_type == "baseline":
        est: Any = LogisticRegression(random_state=seed, solver="lbfgs", **hp)
    elif model_type == "champion":
        est = HistGradientBoostingClassifier(random_state=seed, **hp)
    else:
        raise ValueError(f"unknown model_type {model_type}")
    return Pipeline([("prep", build_preprocessor(spec)), ("model", est)])


@dataclass
class ModelEvaluation:
    model_type: str
    metrics: dict[str, Any]
    calibration: dict[str, Any]
    roc: dict[str, list[float]]
    threshold_analysis: list[dict[str, Any]]
    confusion: dict[str, Any]
    feature_importance: list[dict[str, Any]]
    fairness: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class TrainingResult:
    config: dict[str, Any]
    split_counts: dict[str, int]
    evaluations: dict[str, ModelEvaluation]
    hypothesis_tests: list[dict[str, Any]]
    baseline_distributions: dict[str, Any]
    pipelines: dict[str, Pipeline] = field(repr=False)
    illustrative_threshold: float = 0.5

    def metrics_summary(self) -> dict[str, dict[str, Any]]:
        return {k: v.metrics for k, v in self.evaluations.items()}


def _choose_illustrative_threshold(y: np.ndarray, p: np.ndarray) -> float:
    """F1-maximising threshold on the validation partition. Illustrative only, not policy."""
    best_t, best_f1 = 0.5, -1.0
    for t in np.arange(0.05, 0.95, 0.01):
        f1 = M.confusion_at_threshold(y, p, float(t)).f1
        if f1 > best_f1:
            best_t, best_f1 = float(round(t, 2)), f1
    return best_t


def _feature_importance(pipe: Pipeline, X: pd.DataFrame, y: np.ndarray, seed: int) -> list[dict[str, Any]]:
    """Permutation importance on the holdout (ADR-0005: substituted for SHAP)."""
    r = permutation_importance(pipe, X, y, scoring="roc_auc", n_repeats=10, random_state=seed, n_jobs=1)
    rows = [
        {"feature": f, "importance_mean": float(m), "importance_std": float(s), "method": "permutation_auc"}
        for f, m, s in zip(X.columns, r.importances_mean, r.importances_std, strict=True)
    ]
    return sorted(rows, key=lambda d: -d["importance_mean"])


def evaluate_model(
    model_type: str,
    pipe: Pipeline,
    test: pd.DataFrame,
    threshold: float,
    seed: int,
    n_bootstrap: int,
    fairness_field: str | None,
    spec: FeatureSpec = SYNTHETIC_SPEC,
) -> ModelEvaluation:
    X = test[list(spec.features)]
    y = test["default_flag"].to_numpy(dtype=float)
    p = pipe.predict_proba(X)[:, 1]
    auc_ci = M.bootstrap_ci(y, p, M.auc_roc, n_bootstrap=n_bootstrap, seed=seed)
    ks_ci = M.bootstrap_ci(y, p, M.ks_statistic, n_bootstrap=n_bootstrap, seed=seed)
    cal = M.calibration(y, p, n_bins=10)
    fpr, tpr, _ = M.roc_curve_points(y, p)
    # Downsample the ROC curve for storage/plotting.
    step = max(1, len(fpr) // 200)
    fairness = None
    if fairness_field and fairness_field in test.columns:
        fairness = group_metrics(y, p, test[fairness_field].to_numpy(), threshold)
    return ModelEvaluation(
        model_type=model_type,
        metrics={
            "auc": {"value": auc_ci.point, "lower_ci": auc_ci.lower, "upper_ci": auc_ci.upper},
            "ks": {"value": ks_ci.point, "lower_ci": ks_ci.lower, "upper_ci": ks_ci.upper},
            "brier": {"value": M.brier_score(y, p)},
            "ece": {"value": cal.ece},
            "n_holdout": {"value": float(len(y))},
            "holdout_default_rate": {"value": float(y.mean())},
        },
        calibration=cal.to_dict(),
        roc={"fpr": fpr[::step].round(5).tolist(), "tpr": tpr[::step].round(5).tolist()},
        threshold_analysis=M.threshold_analysis(y, p),
        confusion=M.confusion_at_threshold(y, p, threshold).to_dict(),
        feature_importance=_feature_importance(pipe, X, y, seed),
        fairness=fairness,
    )


def baseline_distributions(
    train: pd.DataFrame, pipe: Pipeline, n_bins: int = 10, spec: FeatureSpec = SYNTHETIC_SPEC
) -> dict[str, Any]:
    """Training-cohort reference distributions consumed by the monitoring PSI checks."""
    out: dict[str, Any] = {"numeric": {}, "categorical": {}, "psi_bins": n_bins}
    for col in spec.numeric:
        edges = numeric_bins(train[col].to_numpy(dtype=float), n_bins)
        counts, _ = np.histogram(train[col].dropna().to_numpy(dtype=float), bins=open_edges(edges))
        out["numeric"][col] = {
            "edges": [float(e) for e in edges],
            "expected_pct": (counts / max(counts.sum(), 1)).round(6).tolist(),
        }
    for col in tuple(spec.categorical) + spec.monitoring_only:
        if col in train.columns:
            vc = train[col].astype(str).value_counts(normalize=True)
            out["categorical"][col] = {str(k): float(v) for k, v in vc.items()}
    scores = pipe.predict_proba(train[list(spec.features)])[:, 1]
    edges = np.linspace(0, 1, 11)
    counts, _ = np.histogram(scores, bins=edges)
    out["scores"] = {
        "edges": [float(e) for e in edges],
        "expected_pct": (counts / max(counts.sum(), 1)).round(6).tolist(),
        "mean": float(scores.mean()),
    }
    out["train_default_rate"] = float(train["default_flag"].mean())
    return out


def train_models(
    df: pd.DataFrame,
    *,
    seed: int = 42,
    data_checksum: str,
    hyperparams: dict[str, dict[str, Any]] | None = None,
    n_bootstrap: int = 300,
    fairness_field: str | None = "fairness_group",
    git_sha: str | None = None,
    spec: FeatureSpec = SYNTHETIC_SPEC,
) -> TrainingResult:
    """Train baseline + champion on a temporal (or documented stratified) split; evaluate on one holdout."""
    if spec is not SYNTHETIC_SPEC:
        fairness_field = spec.fairness_field
    split: SplitResult = choose_split(df, seed, spec.time_field_valid)
    hp = {k: {**DEFAULT_HYPERPARAMS[k], **(hyperparams or {}).get(k, {})} for k in MODEL_TYPES}
    y_train = split.train["default_flag"].to_numpy(dtype=float)
    y_valid = split.validation["default_flag"].to_numpy(dtype=float)
    pipelines: dict[str, Pipeline] = {}
    evaluations: dict[str, ModelEvaluation] = {}
    threshold = 0.5
    for mt in MODEL_TYPES:
        pipe = build_pipeline(mt, seed, hp[mt], spec)
        pipe.fit(split.train[list(spec.features)], y_train)
        pipelines[mt] = pipe
    # Illustrative threshold chosen on validation for the champion; reused for both models.
    p_valid = pipelines["champion"].predict_proba(split.validation[list(spec.features)])[:, 1]
    threshold = _choose_illustrative_threshold(y_valid, p_valid)
    for mt in MODEL_TYPES:
        evaluations[mt] = evaluate_model(
            mt, pipelines[mt], split.test, threshold, seed, n_bootstrap, fairness_field, spec
        )
    ht_feature = spec.numeric[0]
    tests = [
        two_sample_ks(
            split.train[ht_feature].to_numpy(dtype=float),
            split.test[ht_feature].to_numpy(dtype=float),
            ht_feature,
        )
    ]
    config = {
        "random_seed": seed,
        "split": {"strategy": split.strategy, **split.boundaries, "counts": split.counts()},
        "features": list(spec.features),
        "excluded_features": dict(spec.excluded),
        "feature_spec": spec.to_dict(),
        "transformations": {
            "numeric": "median impute -> standard scale",
            "categorical": "most-frequent impute -> one-hot (fixed levels, unknown ignored)",
        },
        "hyperparameters": hp,
        "package_versions": package_versions(),
        "training_data_checksum": data_checksum,
        "n_bootstrap": n_bootstrap,
        "fairness_field": fairness_field,
        "illustrative_threshold": threshold,
        "git_sha": git_sha,
        "python_executable": sys.executable,
    }
    return TrainingResult(
        config=config,
        split_counts=split.counts(),
        evaluations=evaluations,
        hypothesis_tests=tests,
        baseline_distributions=baseline_distributions(split.train, pipelines["champion"], spec=spec),
        pipelines=pipelines,
        illustrative_threshold=threshold,
    )


def save_artifacts(result: TrainingResult, directory: str | Path) -> dict[str, str]:
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for mt, pipe in result.pipelines.items():
        p = d / f"{mt}.joblib"
        joblib.dump(pipe, p)
        paths[f"{mt}_model"] = str(p)
    (d / "metrics.json").write_text(
        json.dumps({k: v.to_dict() for k, v in result.evaluations.items()}, indent=2, default=str)
    )
    (d / "config.json").write_text(json.dumps(result.config, indent=2, default=str))
    (d / "baseline_distributions.json").write_text(json.dumps(result.baseline_distributions, indent=2))
    (d / "hypothesis_tests.json").write_text(json.dumps(result.hypothesis_tests, indent=2))
    paths.update(
        {
            "metrics": str(d / "metrics.json"),
            "config": str(d / "config.json"),
            "baseline_distributions": str(d / "baseline_distributions.json"),
            "hypothesis_tests": str(d / "hypothesis_tests.json"),
        }
    )
    return paths


def load_pipeline(path: str | Path) -> Pipeline:
    return joblib.load(path)

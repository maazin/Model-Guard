"""Discrimination and calibration metrics for a binary PD model.

All functions take plain numpy arrays so they are trivially unit-testable and independent of
any model library. Where scikit-learn offers the same metric we still implement it here so the
formula is explicit and auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import ArrayLike


def _as_arrays(y_true: ArrayLike, y_score: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y_true, dtype=float).ravel()
    s = np.asarray(y_score, dtype=float).ravel()
    if y.shape != s.shape:
        raise ValueError(f"y_true and y_score must align: {y.shape} vs {s.shape}")
    if not np.isin(y, (0.0, 1.0)).all():
        raise ValueError("y_true must be binary 0/1")
    return y, s


def roc_curve_points(y_true: ArrayLike, y_score: ArrayLike) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (fpr, tpr, thresholds) sorted by descending threshold, with the (0,0) origin."""
    y, s = _as_arrays(y_true, y_score)
    order = np.argsort(-s, kind="mergesort")
    y_sorted = s_sorted = None
    y_sorted, s_sorted = y[order], s[order]
    # Collapse ties: only evaluate at the last index of each distinct score.
    distinct = np.where(np.diff(s_sorted))[0]
    idx = np.r_[distinct, y_sorted.size - 1]
    tps = np.cumsum(y_sorted)[idx]
    fps = (1 + idx) - tps
    n_pos, n_neg = y.sum(), y.size - y.sum()
    tpr = np.r_[0.0, tps / n_pos] if n_pos else np.r_[0.0, np.zeros_like(tps, dtype=float)]
    fpr = np.r_[0.0, fps / n_neg] if n_neg else np.r_[0.0, np.zeros_like(fps, dtype=float)]
    thresholds = np.r_[np.inf, s_sorted[idx]]
    return fpr, tpr, thresholds


def auc_roc(y_true: ArrayLike, y_score: ArrayLike) -> float:
    """Area under the ROC curve via the trapezoid rule (equivalent to the Mann-Whitney U form)."""
    y, s = _as_arrays(y_true, y_score)
    if y.sum() == 0 or y.sum() == y.size:
        raise ValueError("AUC undefined when only one class is present")
    fpr, tpr, _ = roc_curve_points(y, s)
    return float(np.trapezoid(tpr, fpr))


def ks_statistic(y_true: ArrayLike, y_score: ArrayLike) -> float:
    """Kolmogorov-Smirnov separation: max over thresholds of (TPR - FPR)."""
    y, s = _as_arrays(y_true, y_score)
    if y.sum() == 0 or y.sum() == y.size:
        raise ValueError("KS undefined when only one class is present")
    fpr, tpr, _ = roc_curve_points(y, s)
    return float(np.max(tpr - fpr))


def brier_score(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    y, p = _as_arrays(y_true, y_prob)
    return float(np.mean((p - y) ** 2))


@dataclass
class CalibrationResult:
    bin_edges: list[float]
    bin_count: list[int]
    mean_predicted: list[float]
    observed_rate: list[float]
    ece: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "bin_edges": self.bin_edges,
            "bin_count": self.bin_count,
            "mean_predicted": self.mean_predicted,
            "observed_rate": self.observed_rate,
            "ece": self.ece,
        }


def calibration(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int = 10) -> CalibrationResult:
    """Equal-width calibration curve and expected calibration error (ECE).

    ECE = sum_b (n_b / N) * |observed_rate_b - mean_predicted_b|. Empty bins are skipped.
    """
    if n_bins < 2:
        raise ValueError("n_bins must be >= 2")
    y, p = _as_arrays(y_true, y_prob)
    if ((p < 0) | (p > 1)).any():
        raise ValueError("probabilities must lie in [0, 1]")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    # np.digitize puts p == 1.0 in the overflow bin, so clip to the last real bin.
    bins = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    counts, mean_pred, obs, ece = [], [], [], 0.0
    for b in range(n_bins):
        mask = bins == b
        n_b = int(mask.sum())
        counts.append(n_b)
        if n_b == 0:
            mean_pred.append(float("nan"))
            obs.append(float("nan"))
            continue
        mp = float(p[mask].mean())
        ob = float(y[mask].mean())
        mean_pred.append(mp)
        obs.append(ob)
        ece += (n_b / y.size) * abs(ob - mp)
    return CalibrationResult(
        bin_edges=[float(e) for e in edges],
        bin_count=counts,
        mean_predicted=mean_pred,
        observed_rate=obs,
        ece=float(ece),
    )


def expected_calibration_error(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int = 10) -> float:
    return calibration(y_true, y_prob, n_bins=n_bins).ece


@dataclass
class ConfusionResult:
    threshold: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    specificity: float
    f1: float
    selection_rate: float

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def confusion_at_threshold(y_true: ArrayLike, y_prob: ArrayLike, threshold: float) -> ConfusionResult:
    y, p = _as_arrays(y_true, y_prob)
    pred = (p >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return ConfusionResult(
        threshold=float(threshold),
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
        precision=precision,
        recall=recall,
        specificity=specificity,
        f1=f1,
        selection_rate=float(pred.mean()) if pred.size else 0.0,
    )


def threshold_analysis(
    y_true: ArrayLike, y_prob: ArrayLike, thresholds: list[float] | None = None
) -> list[dict[str, Any]]:
    """Confusion metrics across a grid of thresholds. Thresholds are illustrative, not policy."""
    grid = thresholds or [round(t, 2) for t in np.arange(0.05, 0.96, 0.05)]
    return [confusion_at_threshold(y_true, y_prob, t).to_dict() for t in grid]


@dataclass
class BootstrapCI:
    point: float
    lower: float
    upper: float
    n_bootstrap: int
    confidence: float
    samples: list[float] = field(default_factory=list, repr=False)


def bootstrap_ci(
    y_true: ArrayLike,
    y_score: ArrayLike,
    metric_fn: Any,
    n_bootstrap: int = 500,
    confidence: float = 0.95,
    seed: int = 42,
) -> BootstrapCI:
    """Percentile bootstrap confidence interval for any (y_true, y_score) -> float metric.

    Resamples rows with replacement; resamples that contain a single class are skipped for
    metrics that are undefined there (AUC/KS), which slightly narrows the interval on tiny data.
    """
    y, s = _as_arrays(y_true, y_score)
    rng = np.random.default_rng(seed)
    point = float(metric_fn(y, s))
    samples: list[float] = []
    n = y.size
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        yb, sb = y[idx], s[idx]
        if yb.sum() == 0 or yb.sum() == n:
            continue
        samples.append(float(metric_fn(yb, sb)))
    if not samples:
        return BootstrapCI(point, point, point, 0, confidence)
    alpha = (1 - confidence) / 2
    lower, upper = np.quantile(samples, [alpha, 1 - alpha])
    return BootstrapCI(point, float(lower), float(upper), len(samples), confidence, samples)

# ADR-0002: Champion model = scikit-learn HistGradientBoostingClassifier

**Status:** Accepted

## Decision

The champion candidate is `sklearn.ensemble.HistGradientBoostingClassifier`; the baseline is an L2 logistic regression. XGBoost was not adopted.

## Rationale

- **Reproducibility and installation:** HGB ships with scikit-learn (already a dependency), builds on every platform we target (macOS arm64, Linux, the Docker image) with no compiled extras, and is deterministic for a fixed `random_state`. XGBoost adds a compiled dependency, an OpenMP runtime requirement on macOS, and version-specific serialisation formats.
- **Single pipeline:** both models share one `ColumnTransformer` -> estimator `Pipeline`, so the artifact used in validation is the artifact used in monitoring (no train/serve skew).
- **Interpretability:** permutation importance (ADR-0005) applies uniformly.

## Consequences

- On the synthetic fixture the champion and baseline are statistically indistinguishable on AUC (differences fall inside the bootstrap CI); the champion is better calibrated (lower ECE). The registry does **not** auto-promote on any metric: a human reviewer decides.
- Hyperparameters are stored per run (`training_runs.config_json`) and can be overridden per request.

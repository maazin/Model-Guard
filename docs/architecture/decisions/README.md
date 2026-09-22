# Architecture decision records

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-dataset-and-license.md) | Dataset and license: UCI 350 (CC BY 4.0, owner-confirmed) plus the in-repo synthetic fixture | Accepted |
| [0002](0002-champion-model.md) | Champion = scikit-learn HistGradientBoosting, not XGBoost | Accepted |
| [0003](0003-temporal-split.md) | Temporal split over stratified | Accepted |
| [0004](0004-target-and-leakage.md) | Target definition and leakage controls | Accepted |
| [0005](0005-feature-importance.md) | Permutation importance substituted for SHAP | Accepted |
| [0006](0006-retrieval-and-llm-provider.md) | TF-IDF local index; rule-based provider mandatory, hosted LLMs optional | Accepted |
| [0007](0007-monitoring-thresholds.md) | PSI/AUC thresholds are configurable defaults, not policy | Accepted |

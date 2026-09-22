# ADR-0005: Permutation importance instead of SHAP

**Status:** Accepted

## Decision

Feature importance is computed with `sklearn.inspection.permutation_importance` (AUC drop, 10 repeats, fixed seed) on the temporal holdout for both models.

## Rationale

- SHAP adds a compiled dependency with historically fragile wheels across Python versions; the portfolio project prioritises "clone and run" reproducibility.
- Permutation importance is model-agnostic, so the baseline and champion are compared with one method.

## Limitation

Permutation importance is confounded by correlated features (e.g. `interest_rate` partly encodes `debt_to_income` in the fixture) and reports global, not local, attributions. A SHAP-based local explanation is a listed follow-up and the provider interface in `modelguard_ml.training._feature_importance` is the single place to swap it in.

---
document_type: model_card
title: Model Card
model_version: pd-credit-v2.0.0
model_uuid: 7ab4aa59-da7f-4440-af8f-77fd62ae6d91
status: complete
template_version: 1
---

# Model Card — pd-credit-v2.0.0

## Model name and version

- Name: ModelGuard PD model (`pd-credit-v2.0.0`), immutable UUID `7ab4aa59-da7f-4440-af8f-77fd62ae6d91`
- Registered model type: **champion** (HistGradientBoostingClassifier)
- Training run: `124a5dda-1ba9-472a-9d7c-8c25893d7d53`; git SHA `0346788e76e844393773b49137f6dddef8196a47`
- Created: 2026-09-22T06:53:25

## Business purpose and intended use

Estimate the probability that a credit-card holder defaults on next month's payment from six months of billing and repayment history, so that portfolio risk can be ranked and monitored. Portfolio simulation on the public UCI 350 dataset; not used for any real lending decision.

## Out-of-scope uses

Credit decisions, pricing, collections prioritisation, any real borrower, and any regulatory reporting.

## Data source, license, and lineage

- Source: `uci-credit-default-2005` — UCI 350 - Default of Credit Card Clients (Yeh & Lien, 2009) (license: https://creativecommons.org/licenses/by/4.0/, retrieved 2026-09-22)
- Snapshot as-of 2005-09-30, 30000 rows, SHA-256 `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933`
- Lineage: source `uci-credit-default-2005` → snapshot `2d0f1d7a-7d7d-497a-a27d-ffa9ece34856` → training run `124a5dda-1ba9-472a-9d7c-8c25893d7d53` → model version `pd-credit-v2.0.0`

## Target definition and modeling approach

`default_flag` = UCI variable `default payment next month` (October 2005). Leakage controls: only April to September 2005 billing/payment history is used; identifiers and demographic fields (sex, age, education, marriage) are excluded from features (ADR-0004); `sex` is retained solely for fairness diagnostics.

Baseline: L2-regularised logistic regression. Champion candidate: scikit-learn
`HistGradientBoostingClassifier` (ADR-0002). Both share one preprocessing pipeline.

## Feature list and excluded-feature rationale

Features: `credit_limit`, `utilization_recent`, `utilization_mean`, `pay_status_recent`, `pay_status_max`, `months_delinquent`, `bill_amt_mean`, `pay_amt_mean`, `pay_to_bill_ratio`

Excluded:
- `loan_id`: Pseudonymous hash of the source ID; identifiers carry no predictive meaning.
- `as_of_date`: Constant (September 2005 snapshot); used only for batch assignment.
- `sex`: Protected characteristic; retained solely for fairness diagnostics, never a feature.
- `age`: Protected/age-related characteristic; excluded from features by design.
- `education`: Socio-economic proxy with unclear coding (levels 0, 5, 6 undocumented); excluded.
- `marriage`: Protected/family-status proxy; excluded from features by design.

## Training/validation split and reproducibility settings

- Split: stratified (train 18000 / validation 6000 / test 6000 rows)
- Random seed: `42`; training-data checksum `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933`
- Hyperparameters: `{"learning_rate": 0.04, "max_iter": 150, "max_depth": 3, "max_leaf_nodes": 8, "min_samples_leaf": 60, "l2_regularization": 5.0, "early_stopping": false}`
- Package versions: `{"python": "3.13.7", "numpy": "2.5.3", "pandas": "3.0.6", "scikit-learn": "1.9.1", "scipy": "1.18.1", "joblib": "1.6.0"}`

## Performance, calibration, and fairness results

Holdout AUC 0.789 [0.776, 0.804], KS 0.438, Brier 0.1318, ECE 0.0111 versus baseline AUC 0.742. Fairness: selection-rate ratio 0.873. Full detail in the validation report.

## Known limitations and failure modes

- Public 2005 Taiwanese credit-card sample (UCI 350); results do not transfer to any other market, period or product.
- No valid time axis, so the split is stratified: there is no out-of-time performance estimate (ADR-0003).
- Holdout of 6000 rows; treat differences inside the bootstrap CI as noise.
- The illustrative threshold is not a credit policy; no lending decision should be derived from it.
- Fairness diagnostics use the `sex` field (never a model feature) and are not a legal determination.

## Monitoring plan and alert thresholds

PSI on every feature and on scores against stored training distributions; defaults stable < 0.1, investigate 0.1–0.25, alert > 0.25; AUC drop > 0.05 when labels arrive. Configurable project defaults, not policy.

## Controls and owners

| Control | Owner | Frequency | Status | Test evidence | Evidence URI |
| --- | --- | --- | --- | --- | --- |
| Copilot data boundary | data_scientist | continuous | tested | prompt-injection and raw-row tests | tests/unit/test_copilot.py |
| Data quality gate | data_scientist | per snapshot | tested | 8 unit tests | tests/unit/test_data_quality.py |
| Hash-chained audit log | reviewer | continuous | tested | tamper detection tests | tests/unit/test_audit_chain.py |
| Human approval gate | reviewer | per version | tested | role enforcement tests | tests/integration/test_lifecycle_api.py |
| Monitoring and alerting | data_scientist | quarterly | implemented | drift alert integration test | apps/api/modelguard_api/services/monitoring.py |
| Reproducible training | data_scientist | per run | tested | deterministic metrics test | tests/unit/test_training.py |

## Approval state and change log

Approval state is maintained in the registry and audit log; see the change log document.
Current state at last render: **VALIDATED**.

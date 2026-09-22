---
document_type: model_card
title: Model Card
model_version: pd-credit-v1.1.0
model_uuid: 7ad1f9c0-912e-4781-b112-2dfd2476d48e
status: complete
template_version: 1
---

# Model Card — pd-credit-v1.1.0

## Model name and version

- Name: ModelGuard PD model (`pd-credit-v1.1.0`), immutable UUID `7ad1f9c0-912e-4781-b112-2dfd2476d48e`
- Registered model type: **champion** (HistGradientBoostingClassifier)
- Training run: `b57abc81-d921-416a-a178-4d0be10a826f`; git SHA `0137b79f8d3e0b6e02539675e132efaa70a20767`
- Created: 2026-09-22T04:37:04

## Business purpose and intended use

Estimate the probability that a consumer instalment loan defaults within the observation window so that portfolio risk can be ranked and monitored. Portfolio simulation only; not used for any real lending decision.

## Out-of-scope uses

Credit decisions, pricing, collections prioritisation, any real borrower, and any regulatory reporting.

## Data source, license, and lineage

- Source: `synthetic-loans-v1` — ModelGuard synthetic loan-performance fixture (license: https://opensource.org/license/mit, retrieved 2026-09-22)
- Snapshot as-of 2023-12-31, 6000 rows, SHA-256 `a68e05490331bb5348c17eb92620715db7eb86ac91f4b1a83ce8b49af353174b`
- Lineage: source `synthetic-loans-v1` → snapshot `5a9cc7ef-5a80-4273-89af-2532a4e252ca` → training run `b57abc81-d921-416a-a178-4d0be10a826f` → model version `pd-credit-v1.1.0`

## Target definition and modeling approach

`default_flag` = 1 when the synthetic borrower defaults within the observation window. Leakage controls: no post-outcome fields exist in the schema; `as_of_date` is used only for the temporal split; identifiers and geography are excluded (ADR-0004).

Baseline: L2-regularised logistic regression. Champion candidate: scikit-learn
`HistGradientBoostingClassifier` (ADR-0002). Both share one preprocessing pipeline.

## Feature list and excluded-feature rationale

Features: `annual_income`, `debt_to_income`, `loan_amount`, `interest_rate`, `term_months`, `credit_history_length`, `employment_length`

Excluded:
- `loan_id`: Identifier; no predictive meaning and would leak record identity.
- `as_of_date`: Used only for temporal splitting and batch assignment.
- `region`: Geographic proxy for protected characteristics; retained for monitoring only.
- `fairness_group`: Synthetic fairness cohort used solely for diagnostics, never as a feature.

## Training/validation split and reproducibility settings

- Split: temporal (train 3437 / validation 1262 / test 1301 rows)
- Random seed: `7`; training-data checksum `a68e05490331bb5348c17eb92620715db7eb86ac91f4b1a83ce8b49af353174b`
- Hyperparameters: `{"learning_rate": 0.03, "max_iter": 200, "max_depth": 3, "max_leaf_nodes": 8, "min_samples_leaf": 60, "l2_regularization": 5.0, "early_stopping": false}`
- Package versions: `{"python": "3.13.7", "numpy": "2.5.3", "pandas": "3.0.6", "scikit-learn": "1.9.1", "scipy": "1.18.1", "joblib": "1.6.0"}`

## Performance, calibration, and fairness results

Holdout AUC 0.762 [0.718, 0.805], KS 0.410, Brier 0.0833, ECE 0.0082 versus baseline AUC 0.771. Fairness: selection-rate ratio 0.892. Full detail in the validation report.

## Known limitations and failure modes

- Data are synthetic (or a licensed public sample); results do not transfer to any real portfolio.
- Temporal split (temporal) over a short window; macro regimes are not represented (ADR-0003).
- Holdout of 1301 rows gives wide confidence intervals; treat differences inside the CI as noise.
- The illustrative threshold is not a credit policy; no lending decision should be derived from it.
- Fairness diagnostics use a synthetic grouping field and are not a legal determination.

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

---
document_type: model_card
title: Model Card
model_version: pd-credit-v1.2.0
model_uuid: d02b129c-327a-47e6-afd5-2cd6b554530f
status: draft
template_version: 1
---

# Model Card — pd-credit-v1.2.0

## Model name and version

- Name: ModelGuard PD model (`pd-credit-v1.2.0`), immutable UUID `d02b129c-327a-47e6-afd5-2cd6b554530f`
- Registered model type: **baseline** (LogisticRegression (L2))
- Training run: `b57abc81-d921-416a-a178-4d0be10a826f`; git SHA `0137b79f8d3e0b6e02539675e132efaa70a20767`
- Created: 2026-09-22T04:37:05

## Business purpose and intended use

TODO

## Out-of-scope uses

TODO

## Data source, license, and lineage

- Source: `synthetic-loans-v1` — ModelGuard synthetic loan-performance fixture (license: https://opensource.org/license/mit, retrieved 2026-09-22)
- Snapshot as-of 2023-12-31, 6000 rows, SHA-256 `a68e05490331bb5348c17eb92620715db7eb86ac91f4b1a83ce8b49af353174b`
- Lineage: source `synthetic-loans-v1` → snapshot `5a9cc7ef-5a80-4273-89af-2532a4e252ca` → training run `b57abc81-d921-416a-a178-4d0be10a826f` → model version `pd-credit-v1.2.0`

## Target definition and modeling approach

TODO

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
- Hyperparameters: `{"C": 1.0, "max_iter": 2000, "class_weight": null}`
- Package versions: `{"python": "3.13.7", "numpy": "2.5.3", "pandas": "3.0.6", "scikit-learn": "1.9.1", "scipy": "1.18.1", "joblib": "1.6.0"}`

## Performance, calibration, and fairness results

Holdout AUC 0.771 [0.725, 0.811], KS 0.410, Brier 0.0828, ECE 0.0134 versus champion AUC 0.762. Fairness: selection-rate ratio 0.937. Full detail in the validation report.

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
| Data quality gate | data_scientist | per snapshot | tested | 8 unit tests | tests/unit/test_data_quality.py |
| Reproducible training | data_scientist | per run | tested | deterministic metrics test | tests/unit/test_training.py |

## Approval state and change log

Approval state is maintained in the registry and audit log; see the change log document.
Current state at last render: **VALIDATED**.

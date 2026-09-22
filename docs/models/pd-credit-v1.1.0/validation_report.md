---
document_type: validation_report
title: Validation Report
model_version: pd-credit-v1.1.0
status: complete
template_version: 1
---

# Validation Report — pd-credit-v1.1.0

Each metric below states what was tested, the result, interpretation, limitation, the artifact
that holds the full output, and reviewer status.

## Scope

Holdout evaluation of the registered **champion** model against the logistic baseline on
the temporally later test partition (1301 rows). Illustrative threshold
`0.22` was chosen on the validation partition to maximise F1; it is **not** a lending
policy.

## Discrimination

| Metric | champion (registered) | baseline |
| --- | --- | --- |
| AUC-ROC (95% bootstrap CI) | 0.7624 [0.7180, 0.8049] | 0.7706 |
| KS (95% bootstrap CI) | 0.4096 [0.3579, 0.4849] | 0.4100 |
| Brier score | 0.0833 | 0.0828 |
| ECE (10 bins) | 0.0082 | 0.0134 |

Holdout rows: 1301; holdout default rate 0.104. Interpretation: AUC/KS measure rank ordering; Brier/ECE measure probability quality. Limitation: bootstrap resamples the temporal holdout only (300 draws); no cross-period stability claim. Artifact: `artifacts/runs/4dd2b2d2-9818-4fff-b9df-ff237f74a872/metrics.json`. Reviewer status: pending.

## Calibration

ECE = 0.0082 over 10 equal-width bins (configurable).

| Bin | n | Mean predicted | Observed |
| --- | --- | --- | --- |
| 1 | 851 | 0.047 | 0.052 |
| 2 | 298 | 0.139 | 0.148 |
| 3 | 89 | 0.241 | 0.247 |
| 4 | 38 | 0.347 | 0.368 |
| 5 | 13 | 0.437 | 0.308 |
| 6 | 10 | 0.560 | 0.500 |
| 7 | 2 | 0.653 | 1.000 |

Interpretation: bins near the diagonal indicate well-calibrated PDs. Limitation: sparse high-score bins are noisy. Reviewer status: pending.

## Threshold analysis

Illustrative threshold 0.22 (F1-optimal on validation; **not a lending policy**): TP 44, FP 84, TN 1082, FN 91; precision 0.344, recall 0.326, selection rate 0.098. Full grid stored as the `threshold_analysis` artifact. Reviewer status: pending.

## Feature importance

Permutation importance (AUC drop, 10 repeats; ADR-0005):

| Feature | Mean | Std |
| --- | --- | --- |
| `debt_to_income` | 0.0988 | 0.0172 |
| `credit_history_length` | 0.0396 | 0.0080 |
| `annual_income` | 0.0138 | 0.0047 |
| `interest_rate` | 0.0130 | 0.0064 |
| `term_months` | 0.0127 | 0.0041 |
| `loan_amount` | 0.0107 | 0.0022 |
| `employment_length` | 0.0093 | 0.0021 |

Limitation: permutation importance is confounded by correlated features. Reviewer status: pending.

## Hypothesis test

Two-sample KS test on `annual_income` (train vs. temporal holdout): D = 0.0391, p = 0.1088, Cohen's d = -0.0386, n = 3437 / 1301. H0 not rejected at α = 0.05. Assumptions: independent samples, continuous variable, no ties correction needed. Limitation: Large samples make small shifts statistically significant; interpret alongside the effect size and PSI, and note the test ignores time ordering within cohorts. Reviewer status: pending.

## Fairness diagnostics

Synthetic `fairness_group` cohorts at threshold 0.22: selection-rate ratio 0.892, TPR difference 0.085, FPR difference 0.003.

| Group | n | Selection rate | TPR | FPR | Observed default | Mean predicted |
| --- | --- | --- | --- | --- | --- | --- |
| A | 788 | 0.094 | 0.293 | 0.071 | 0.104 | 0.099 |
| B | 513 | 0.105 | 0.377 | 0.074 | 0.103 | 0.099 |

Diagnostic only. Computed on an explicitly approved grouping field that is never a model feature; not a legal or regulatory fairness determination. Reviewer status: pending.

## Limitations

- Data are synthetic (or a licensed public sample); results do not transfer to any real portfolio.
- Temporal split (temporal) over a short window; macro regimes are not represented (ADR-0003).
- Holdout of 1301 rows gives wide confidence intervals; treat differences inside the CI as noise.
- The illustrative threshold is not a credit policy; no lending decision should be derived from it.
- Fairness diagnostics use a synthetic grouping field and are not a legal determination.

## Reviewer status

Pending human review. Approval state is tracked in the registry.

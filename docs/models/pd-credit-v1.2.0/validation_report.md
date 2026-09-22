---
document_type: validation_report
title: Validation Report
model_version: pd-credit-v1.2.0
status: draft
template_version: 1
---

# Validation Report — pd-credit-v1.2.0

Each metric below states what was tested, the result, interpretation, limitation, the artifact
that holds the full output, and reviewer status.

## Scope

Holdout evaluation of the registered **baseline** model against the logistic baseline on
the temporally later test partition (1301 rows). Illustrative threshold
`0.22` was chosen on the validation partition to maximise F1; it is **not** a lending
policy.

## Discrimination

| Metric | baseline (registered) | champion |
| --- | --- | --- |
| AUC-ROC (95% bootstrap CI) | 0.7706 [0.7255, 0.8115] | 0.7624 |
| KS (95% bootstrap CI) | 0.4100 [0.3517, 0.4958] | 0.4096 |
| Brier score | 0.0828 | 0.0833 |
| ECE (10 bins) | 0.0134 | 0.0082 |

Holdout rows: 1301; holdout default rate 0.104. Interpretation: AUC/KS measure rank ordering; Brier/ECE measure probability quality. Limitation: bootstrap resamples the temporal holdout only (300 draws); no cross-period stability claim. Artifact: `artifacts/runs/48c775d6-442a-4221-b122-a26d69e4dbbf/metrics.json`. Reviewer status: pending.

## Calibration

ECE = 0.0134 over 10 equal-width bins (configurable).

| Bin | n | Mean predicted | Observed |
| --- | --- | --- | --- |
| 1 | 839 | 0.045 | 0.045 |
| 2 | 287 | 0.142 | 0.150 |
| 3 | 108 | 0.242 | 0.287 |
| 4 | 43 | 0.335 | 0.209 |
| 5 | 13 | 0.452 | 0.692 |
| 6 | 8 | 0.529 | 0.375 |
| 7 | 3 | 0.654 | 0.667 |

Interpretation: bins near the diagonal indicate well-calibrated PDs. Limitation: sparse high-score bins are noisy. Reviewer status: pending.

## Threshold analysis

Illustrative threshold 0.22 (F1-optimal on validation; **not a lending policy**): TP 47, FP 92, TN 1074, FN 88; precision 0.338, recall 0.348, selection rate 0.107. Full grid stored as the `threshold_analysis` artifact. Reviewer status: pending.

## Feature importance

Permutation importance (AUC drop, 10 repeats; ADR-0005):

| Feature | Mean | Std |
| --- | --- | --- |
| `debt_to_income` | 0.1288 | 0.0174 |
| `credit_history_length` | 0.0277 | 0.0072 |
| `annual_income` | 0.0140 | 0.0028 |
| `term_months` | 0.0105 | 0.0046 |
| `loan_amount` | 0.0082 | 0.0028 |
| `employment_length` | 0.0075 | 0.0033 |
| `interest_rate` | 0.0060 | 0.0049 |

Limitation: permutation importance is confounded by correlated features. Reviewer status: pending.

## Hypothesis test

Two-sample KS test on `annual_income` (train vs. temporal holdout): D = 0.0391, p = 0.1088, Cohen's d = -0.0386, n = 3437 / 1301. H0 not rejected at α = 0.05. Assumptions: independent samples, continuous variable, no ties correction needed. Limitation: Large samples make small shifts statistically significant; interpret alongside the effect size and PSI, and note the test ignores time ordering within cohorts. Reviewer status: pending.

## Fairness diagnostics

Synthetic `fairness_group` cohorts at threshold 0.22: selection-rate ratio 0.937, TPR difference 0.048, FPR difference 0.003.

| Group | n | Selection rate | TPR | FPR | Observed default | Mean predicted |
| --- | --- | --- | --- | --- | --- | --- |
| A | 788 | 0.104 | 0.329 | 0.078 | 0.104 | 0.100 |
| B | 513 | 0.111 | 0.377 | 0.080 | 0.103 | 0.102 |

Diagnostic only. Computed on an explicitly approved grouping field that is never a model feature; not a legal or regulatory fairness determination. Reviewer status: pending.

## Limitations

- Synthetic data; results do not transfer to any real portfolio.
- Temporal split over a short window; macro regimes are not represented (ADR-0003).
- Holdout of 1301 rows; treat differences inside the bootstrap CI as noise.
- The illustrative threshold is not a credit policy; no lending decision should be derived from it.
- Fairness diagnostics use the `fairness_group` field (synthetic cohort) and are not a legal determination.

## Reviewer status

Pending human review. Approval state is tracked in the registry.

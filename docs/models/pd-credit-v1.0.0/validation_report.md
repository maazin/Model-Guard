---
document_type: validation_report
title: Validation Report
model_version: pd-credit-v1.0.0
status: complete
template_version: 1
---

# Validation Report — pd-credit-v1.0.0

Each metric below states what was tested, the result, interpretation, limitation, the artifact
that holds the full output, and reviewer status.

## Scope

Holdout evaluation of the registered **champion** model against the logistic baseline on
the temporally later test partition (1301 rows). Illustrative threshold
`0.21` was chosen on the validation partition to maximise F1; it is **not** a lending
policy.

## Discrimination

| Metric | champion (registered) | baseline |
| --- | --- | --- |
| AUC-ROC (95% bootstrap CI) | 0.7638 [0.7227, 0.8007] | 0.7706 |
| KS (95% bootstrap CI) | 0.4094 [0.3567, 0.4880] | 0.4100 |
| Brier score | 0.0832 | 0.0828 |
| ECE (10 bins) | 0.0086 | 0.0134 |

Holdout rows: 1301; holdout default rate 0.104. Interpretation: AUC/KS measure rank ordering; Brier/ECE measure probability quality. Limitation: bootstrap resamples the temporal holdout only (300 draws); no cross-period stability claim. Artifact: `artifacts/runs/63350985-70f3-474b-9ccd-21cbddc1a87d/metrics.json`. Reviewer status: pending.

## Calibration

ECE = 0.0086 over 10 equal-width bins (configurable).

| Bin | n | Mean predicted | Observed |
| --- | --- | --- | --- |
| 1 | 850 | 0.047 | 0.051 |
| 2 | 298 | 0.138 | 0.144 |
| 3 | 90 | 0.244 | 0.267 |
| 4 | 37 | 0.349 | 0.378 |
| 5 | 14 | 0.438 | 0.286 |
| 6 | 10 | 0.558 | 0.500 |
| 7 | 2 | 0.652 | 1.000 |

Interpretation: bins near the diagonal indicate well-calibrated PDs. Limitation: sparse high-score bins are noisy. Reviewer status: pending.

## Threshold analysis

Illustrative threshold 0.21 (F1-optimal on validation; **not a lending policy**): TP 45, FP 94, TN 1072, FN 90; precision 0.324, recall 0.333, selection rate 0.107. Full grid stored as the `threshold_analysis` artifact. Reviewer status: pending.

## Feature importance

Permutation importance (AUC drop, 10 repeats; ADR-0005):

| Feature | Mean | Std |
| --- | --- | --- |
| `debt_to_income` | 0.1075 | 0.0146 |
| `credit_history_length` | 0.0359 | 0.0027 |
| `annual_income` | 0.0155 | 0.0024 |
| `loan_amount` | 0.0139 | 0.0045 |
| `term_months` | 0.0121 | 0.0029 |
| `interest_rate` | 0.0105 | 0.0067 |
| `employment_length` | 0.0102 | 0.0027 |

Limitation: permutation importance is confounded by correlated features. Reviewer status: pending.

## Hypothesis test

Two-sample KS test on `annual_income` (train vs. temporal holdout): D = 0.0391, p = 0.1088, Cohen's d = -0.0386, n = 3437 / 1301. H0 not rejected at α = 0.05. Assumptions: independent samples, continuous variable, no ties correction needed. Limitation: Large samples make small shifts statistically significant; interpret alongside the effect size and PSI, and note the test ignores time ordering within cohorts. Reviewer status: pending.

## Fairness diagnostics

Synthetic `fairness_group` cohorts at threshold 0.21: selection-rate ratio 0.857, TPR difference 0.072, FPR difference 0.010.

| Group | n | Selection rate | TPR | FPR | Observed default | Mean predicted |
| --- | --- | --- | --- | --- | --- | --- |
| A | 788 | 0.100 | 0.305 | 0.076 | 0.104 | 0.099 |
| B | 513 | 0.117 | 0.377 | 0.087 | 0.103 | 0.099 |

Diagnostic only. Computed on an explicitly approved grouping field that is never a model feature; not a legal or regulatory fairness determination. Reviewer status: pending.

## Limitations

- Synthetic data; results do not transfer to any real portfolio.
- Temporal split over a short window; macro regimes are not represented (ADR-0003).
- Holdout of 1301 rows; treat differences inside the bootstrap CI as noise.
- The illustrative threshold is not a credit policy; no lending decision should be derived from it.
- Fairness diagnostics use the `fairness_group` field (synthetic cohort) and are not a legal determination.

## Reviewer status

Pending human review. Approval state is tracked in the registry.

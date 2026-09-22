---
document_type: validation_report
title: Validation Report
model_version: pd-credit-v2.0.0
status: complete
template_version: 1
---

# Validation Report — pd-credit-v2.0.0

Each metric below states what was tested, the result, interpretation, limitation, the artifact
that holds the full output, and reviewer status.

## Scope

Holdout evaluation of the registered **champion** model against the logistic baseline on
the stratified random test partition (the source has no valid time axis) (6000 rows). Illustrative threshold
`0.3` was chosen on the validation partition to maximise F1; it is **not** a lending
policy.

## Discrimination

| Metric | champion (registered) | baseline |
| --- | --- | --- |
| AUC-ROC (95% bootstrap CI) | 0.7894 [0.7757, 0.8038] | 0.7417 |
| KS (95% bootstrap CI) | 0.4378 [0.4185, 0.4717] | 0.4151 |
| Brier score | 0.1318 | 0.1404 |
| ECE (10 bins) | 0.0111 | 0.0271 |

Holdout rows: 6000; holdout default rate 0.221. Interpretation: AUC/KS measure rank ordering; Brier/ECE measure probability quality. Limitation: bootstrap resamples the temporal holdout only (300 draws); no cross-period stability claim. Artifact: `artifacts/runs/1d4f5f96-2042-4b88-a0e8-00bfc8c4f59d/metrics.json`. Reviewer status: pending.

## Calibration

ECE = 0.0111 over 10 equal-width bins (configurable).

| Bin | n | Mean predicted | Observed |
| --- | --- | --- | --- |
| 1 | 1710 | 0.072 | 0.063 |
| 2 | 2266 | 0.143 | 0.142 |
| 3 | 716 | 0.239 | 0.228 |
| 4 | 445 | 0.348 | 0.396 |
| 5 | 191 | 0.449 | 0.466 |
| 6 | 102 | 0.552 | 0.510 |
| 7 | 246 | 0.662 | 0.659 |
| 8 | 289 | 0.745 | 0.779 |
| 9 | 35 | 0.807 | 0.857 |

Interpretation: bins near the diagonal indicate well-calibrated PDs. Limitation: sparse high-score bins are noisy. Reviewer status: pending.

## Threshold analysis

Illustrative threshold 0.30 (F1-optimal on validation; **not a lending policy**): TP 734, FP 574, TN 4099, FN 593; precision 0.561, recall 0.553, selection rate 0.218. Full grid stored as the `threshold_analysis` artifact. Reviewer status: pending.

## Feature importance

Permutation importance (AUC drop, 10 repeats; ADR-0005):

| Feature | Mean | Std |
| --- | --- | --- |
| `pay_status_max` | 0.0476 | 0.0039 |
| `pay_status_recent` | 0.0258 | 0.0019 |
| `bill_amt_mean` | 0.0169 | 0.0030 |
| `utilization_recent` | 0.0115 | 0.0013 |
| `credit_limit` | 0.0081 | 0.0013 |
| `months_delinquent` | 0.0052 | 0.0009 |
| `pay_to_bill_ratio` | 0.0046 | 0.0009 |
| `pay_amt_mean` | 0.0044 | 0.0015 |
| `utilization_mean` | 0.0013 | 0.0006 |

Limitation: permutation importance is confounded by correlated features. Reviewer status: pending.

## Hypothesis test

Two-sample KS test on `credit_limit` (train vs. temporal holdout): D = 0.0103, p = 0.7185, Cohen's d = 0.0069, n = 18000 / 6000. H0 not rejected at α = 0.05. Assumptions: independent samples, continuous variable, no ties correction needed. Limitation: Large samples make small shifts statistically significant; interpret alongside the effect size and PSI, and note the test ignores time ordering within cohorts. Reviewer status: pending.

## Fairness diagnostics

Synthetic `fairness_group` cohorts at threshold 0.30: selection-rate ratio 0.873, TPR difference 0.020, FPR difference 0.026.

| Group | n | Selection rate | TPR | FPR | Observed default | Mean predicted |
| --- | --- | --- | --- | --- | --- | --- |
| female | 3628 | 0.206 | 0.562 | 0.113 | 0.208 | 0.217 |
| male | 2372 | 0.236 | 0.542 | 0.139 | 0.241 | 0.226 |

Diagnostic only. Computed on an explicitly approved grouping field that is never a model feature; not a legal or regulatory fairness determination. Reviewer status: pending.

## Limitations

- Public 2005 Taiwanese credit-card sample (UCI 350); results do not transfer to any other market, period or product.
- No valid time axis, so the split is stratified: there is no out-of-time performance estimate (ADR-0003).
- Holdout of 6000 rows; treat differences inside the bootstrap CI as noise.
- The illustrative threshold is not a credit policy; no lending decision should be derived from it.
- Fairness diagnostics use the `sex` field (never a model feature) and are not a legal determination.

## Reviewer status

Pending human review. Approval state is tracked in the registry.

---
title: Executive risk memo — pd-credit-v2.0.0
generated: 2026-09-22
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Executive risk memo — ModelGuard PD model pd-credit-v2.0.0

> Portfolio simulation. Not credit advice, not a production lending system, and not a compliance claim. Data source: `uci-credit-default-2005`.

## Decision requested

Do not extend use; investigate high-severity drift alerts and consider re-training with recent data.

## What the model is

Estimate the probability that a credit-card holder defaults on next month's payment from six months of billing and repayment history, so that portfolio risk can be ranked and monitored. Portfolio simulation on the public UCI 350 dataset; not used for any real lending decision. Data source `uci-credit-default-2005`. Registered type **champion** (gradient-boosted trees) compared against a logistic-regression baseline on a stratified holdout of 6000 loans.

## Current health: **at risk** (state MONITORING)

| Measure | champion | baseline |
| --- | --- | --- |
| AUC (95% bootstrap CI) | 0.789 [0.776, 0.804] | 0.742 [0.726, 0.758] |
| KS | 0.438 | 0.415 |
| Brier | 0.1318 | 0.1404 |
| ECE | 0.0111 | 0.0271 |

Fairness diagnostics on the `sex` grouping field: selection-rate ratio 0.873, TPR difference 0.020, FPR difference 0.026 (informational only).

## Monitoring (3 quarterly batches)

| Batch | Status | AUC | Max feature PSI | Score PSI |
| --- | --- | --- | --- | --- |
| 2005-12-31 | investigate | 0.801 | 0.004 | 0.001 |
| 2006-03-31 | alert | 0.799 | 0.335 | 0.011 |
| 2006-06-30 | alert | 0.740 | 0.818 | 0.356 |

13 alerts raised (7 high severity); 0 resolved with a recorded rationale. Top open risks: PSI alert on pay_to_bill_ratio (0.335); PSI alert on utilization_recent (0.274); PSI alert on pay_status_recent (0.458).

## Governance evidence

- Readiness: 8/8 deterministic checks pass; 6 controls recorded with owner, frequency and test evidence.
- Registry: 4 model versions, 3 training runs, 8 data snapshots, 189 hash-chained audit events (chain verified).

| Version | Type | State |
| --- | --- | --- |
| pd-credit-v1.0.0 | champion | MONITORING |
| pd-credit-v1.1.0 | champion | PENDING_REVIEW |
| pd-credit-v1.2.0 | baseline | VALIDATED |
| pd-credit-v2.0.0 | champion | MONITORING |

## Limits

- Not credit advice: the cut-off shown is illustrative, not a lending policy.
- Built on a public sample or synthetic data; results do not transfer to a real portfolio.
- Fairness figures are for discussion, not a legal determination.
- Approval here is a simulated governance step, not regulatory compliance.

## Recommended next action

Work open alerts; resolve or escalate before the due date.

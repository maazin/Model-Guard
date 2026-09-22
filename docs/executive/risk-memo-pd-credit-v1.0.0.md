---
title: Executive risk memo — pd-credit-v1.0.0
generated: 2026-09-22
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Executive risk memo — ModelGuard PD model pd-credit-v1.0.0

> Portfolio simulation. Not credit advice, not a production lending system, and not a compliance claim. Data source: `synthetic-loans-v1`.

## Decision requested

Do not extend use; investigate high-severity drift alerts and consider re-training with recent data.

## What the model is

Estimate the probability that a consumer instalment loan defaults within the observation window so that portfolio risk can be ranked and monitored. Portfolio simulation only; not used for any real lending decision. Data source `synthetic-loans-v1`. Registered type **champion** (gradient-boosted trees) compared against a logistic-regression baseline on a temporal holdout of 1301 loans.

## Current health: **at risk** (state MONITORING)

| Measure | champion | baseline |
| --- | --- | --- |
| AUC (95% bootstrap CI) | 0.764 [0.723, 0.801] | 0.771 [0.732, 0.809] |
| KS | 0.409 | 0.410 |
| Brier | 0.0832 | 0.0828 |
| ECE | 0.0086 | 0.0134 |

Fairness diagnostics on the `fairness_group` grouping field: selection-rate ratio 0.857, TPR difference 0.072, FPR difference 0.010 (informational only).

## Monitoring (3 quarterly batches)

| Batch | Status | AUC | Max feature PSI | Score PSI |
| --- | --- | --- | --- | --- |
| 2024-03-31 | ok | 0.721 | 0.015 | 0.005 |
| 2024-06-30 | investigate | 0.762 | 0.210 | 0.103 |
| 2024-09-30 | alert | 0.731 | 3.430 | 1.409 |

8 alerts raised (4 high severity); 1 resolved with a recorded rationale. Top open risks: PSI alert on debt_to_income (1.274); PSI alert on interest_rate (3.430); PSI alert on employment_length (0.354).

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

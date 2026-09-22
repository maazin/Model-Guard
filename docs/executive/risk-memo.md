---
title: Executive risk memo — pd-credit-v1.0.0
generated: 2026-09-22
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Executive risk memo — ModelGuard PD model pd-credit-v1.0.0

> Portfolio simulation on a synthetic dataset. Not credit advice, not a production lending system, and not a compliance claim.

## Decision requested

Do not extend use; investigate high-severity drift alerts and consider re-training with recent data.

## What the model is

Probability-of-default scoring on a licensed/synthetic loan-performance dataset. Portfolio simulation; not a lending decision engine. Registered type **champion** (gradient-boosted trees) compared against a logistic-regression baseline on a temporally later holdout of 1301 loans.

## Current health: **at risk** (state MONITORING)

| Measure | champion | baseline |
| --- | --- | --- |
| AUC (95% bootstrap CI) | 0.764 [0.723, 0.801] | 0.771 [0.732, 0.809] |
| KS | 0.409 | 0.410 |
| Brier | 0.0832 | 0.0828 |
| ECE | 0.0086 | 0.0134 |

Fairness diagnostics on the synthetic grouping field: selection-rate ratio 0.857, TPR difference 0.072, FPR difference 0.010 (informational only).

## Monitoring (3 quarterly batches)

| Batch | Status | AUC | Max feature PSI | Score PSI |
| --- | --- | --- | --- | --- |
| 2024-03-31 | ok | 0.721 | 0.015 | 0.005 |
| 2024-06-30 | investigate | 0.762 | 0.210 | 0.103 |
| 2024-09-30 | alert | 0.731 | 3.430 | 1.409 |

8 alerts raised (4 high severity); 1 resolved with a recorded rationale. Top open risks: PSI alert on debt_to_income (1.274); PSI alert on interest_rate (3.430); PSI alert on employment_length (0.354).

## Governance evidence

- Readiness: 8/8 deterministic checks pass; 6 controls recorded with owner, frequency and test evidence.
- Registry: 3 model versions, 2 training runs, 4 data snapshots, 128 hash-chained audit events (chain verified).

| Version | Type | State |
| --- | --- | --- |
| pd-credit-v1.0.0 | champion | MONITORING |
| pd-credit-v1.1.0 | champion | PENDING_REVIEW |
| pd-credit-v1.2.0 | baseline | VALIDATED |

## Limits

- Not credit advice; illustrative threshold only.
- Synthetic or public sample data; results do not transfer to a real book.
- Fairness diagnostics are informational, not a legal determination.

## Recommended next action

Work open alerts; resolve or escalate before the due date.

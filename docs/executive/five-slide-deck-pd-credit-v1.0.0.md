---
title: ModelGuard — five-slide executive deck
generated: 2026-09-22
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Slide 1 — Why ModelGuard

- One place to develop, validate, approve, monitor and document a PD model.
- Portfolio simulation on `synthetic-loans-v1`; every control is real, every number is measured.
- Human approval gate, hash-chained audit log, offline governance copilot.

---

# Slide 2 — Model performance (pd-credit-v1.0.0, temporal holdout)

| | champion | baseline |
| --- | --- | --- |
| AUC | 0.764 [0.723, 0.801] | 0.771 |
| KS | 0.409 | 0.410 |
| Brier / ECE | 0.0832 / 0.0086 | 0.0828 / 0.0134 |

Differences sit inside the confidence interval; promotion was a human decision, not a metric race.

---

# Slide 3 — Governance package

- 8/8 readiness checks pass; an incomplete version (pd-credit-v1.2.0) is blocked with named gaps.
- 6 controls with owners and test evidence; 8 versioned documents per model.
- 189 audit events in a verified SHA-256 chain.

---

# Slide 4 — Monitoring

| Batch | Status | AUC | Max PSI | Score PSI |
| --- | --- | --- | --- | --- |
| 2024-03-31 | ok | 0.721 | 0.015 | 0.005 |
| 2024-06-30 | investigate | 0.762 | 0.210 | 0.103 |
| 2024-09-30 | alert | 0.731 | 3.430 | 1.409 |

8 alerts (4 high); 1 resolved with rationale. Thresholds are configurable defaults, not policy.

---

# Slide 5 — Recommendation and limits

- **Do not extend use; investigate high-severity drift alerts and consider re-training with recent data.**
- Synthetic data; results do not transfer to a real book.
- Illustrative threshold only; fairness diagnostics are informational.
- Next: Work open alerts; resolve or escalate before the due date.

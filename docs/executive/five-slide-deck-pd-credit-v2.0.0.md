---
title: ModelGuard — five-slide executive deck
generated: 2026-09-22
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Slide 1 — Why ModelGuard

- One place to develop, validate, approve, monitor and document a PD model.
- Portfolio simulation on `uci-credit-default-2005`; every control is real, every number is measured.
- Human approval gate, hash-chained audit log, offline governance copilot.

---

# Slide 2 — Model performance (pd-credit-v2.0.0, stratified holdout)

| | champion | baseline |
| --- | --- | --- |
| AUC | 0.789 [0.776, 0.804] | 0.742 |
| KS | 0.438 | 0.415 |
| Brier / ECE | 0.1318 / 0.0111 | 0.1404 / 0.0271 |

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
| 2005-12-31 | investigate | 0.801 | 0.004 | 0.001 |
| 2006-03-31 | alert | 0.799 | 0.335 | 0.011 |
| 2006-06-30 | alert | 0.740 | 0.818 | 0.356 |

13 alerts (7 high); 0 resolved with rationale. Thresholds are configurable defaults, not policy.

---

# Slide 5 — Recommendation and limits

- **Do not extend use; investigate high-severity drift alerts and consider re-training with recent data.**
- Public 2005 Taiwanese credit-card data; results do not transfer to a real book.
- Illustrative threshold only; fairness diagnostics are informational.
- Next: Work open alerts; resolve or escalate before the due date.

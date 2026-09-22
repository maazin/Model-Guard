# ADR-0007: Monitoring thresholds are configurable defaults

**Status:** Accepted

## Decision

Default thresholds live in `modelguard_shared.constants` and each version's monitoring-plan front matter:

| Signal | Default | Meaning |
| --- | --- | --- |
| PSI (feature or score) | < 0.10 stable · 0.10–0.25 investigate · > 0.25 alert | widely used practitioner rule of thumb |
| AUC drop vs. holdout | > 0.05 | performance alert when labels are available |
| Null rate / duplicate rate | > 5% / > 1% | data-quality alert |
| Observed − predicted default rate | > 5 pp | calibration alert |
| Selection-rate ratio | < 0.80 | fairness diagnostic (four-fifths rule of thumb) |

## Rationale

These are conventions, not regulation. Presenting them as policy would be exactly the kind of fabricated compliance claim the PRD forbids. Making them per-version front matter lets a reviewer see, and change, the thresholds that produced every alert, and the readiness engine refuses a monitoring plan that does not state them.

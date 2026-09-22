# ADR-0004: Target definition and leakage controls

**Status:** Accepted

## Decision

- Target `default_flag` is a binary indicator defined **per data source** in `docs/data-sources/<id>.md`. For the synthetic fixture it is drawn from a logistic process over the documented features.
- Leakage controls:
  1. The normalised schema contains no post-outcome fields (balances after default, collections activity, charge-off amounts).
  2. `as_of_date` is used only for the temporal split and batch assignment; it is never a feature.
  3. `loan_id`, `region` and `fairness_group` are excluded from the feature list (`modelguard_shared.constants.EXCLUDED_FEATURES`) with a rationale that is rendered into every model card.
  4. Data-quality checks enforce the schema before training, so an unexpected column cannot silently enter the feature set.
  5. The feature list is stored with every training run and compared in the readiness engine's lineage check.

# Synthetic fixtures

`synthetic_loans.csv` (6,000 rows, 24 monthly cohorts) and `monitoring/batch_*.csv` (3 quarterly batches with
increasing, deliberately induced drift) are generated deterministically by `scripts/generate_fixtures.py`
using `modelguard_ml.synthetic`. They contain no real borrowers; `loan_id` is a hash of the row index.
`fairness_group` is a synthetic A/B cohort that exists only to exercise the fairness diagnostics.

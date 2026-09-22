---
document_type: data_lineage
title: Data Lineage and Data Dictionary
model_version: pd-credit-v1.2.0
status: draft
template_version: 1
---

# Data Lineage and Data Dictionary — pd-credit-v1.2.0

## Source

- Source ID: `synthetic-loans-v1` (ModelGuard synthetic loan-performance fixture)
- License: https://opensource.org/license/mit; intended use: Offline development, tests and the local demo of the ModelGuard lifecycle. Not derived from real consumers.
- Retrieval date: 2026-09-22; source document: `docs/data-sources/synthetic-loans-v1.md`

## Lineage chain

source `synthetic-loans-v1` → snapshot `5d5cba45-1902-43d6-933f-c26c34f5f954` (as-of 2023-12-31, checksum `a68e05490331bb5348c17eb92620715db7eb86ac91f4b1a83ce8b49af353174b`) → training run `4d36e015-e397-42fa-b05a-5df92521337b` → model version `pd-credit-v1.2.0`

## Data dictionary

| Source field | Normalised field | Type | Allowed range | Transformation | Feature use |
| --- | --- | --- | --- | --- | --- |
| loan_id | loan_id | string | pseudonymous hash | none | excluded (identifier) |
| as_of_date | as_of_date | date | 2022-01 .. 2023-12 | parsed to date | split/batch only |
| default_flag | default_flag | boolean | {0,1} | none | target |
| annual_income | annual_income | numeric | 0 – 5,000,000 | median impute, standard scale | feature |
| debt_to_income | debt_to_income | numeric | 0 – 100 | median impute, standard scale | feature |
| loan_amount | loan_amount | numeric | 100 – 1,000,000 | median impute, standard scale | feature |
| interest_rate | interest_rate | numeric | 0 – 60 | median impute, standard scale | feature |
| term_months | term_months | integer | 6 – 480 | median impute, standard scale | feature |
| employment_length | employment_length | categorical | 5 fixed levels | one-hot | feature |
| credit_history_length | credit_history_length | numeric | 0 – 80 | median impute, standard scale | feature |
| region | region | categorical | 4 levels | none | excluded; monitoring only |
| fairness_group | fairness_group | categorical | synthetic A/B | none | excluded; fairness diagnostics only |

## Quality results

- Status: **pass**; rows 6000; duplicate rate 0.00%; target rate 0.10466666666666667
- No issues raised.

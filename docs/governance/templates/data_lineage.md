---
document_type: data_lineage
title: Data Lineage and Data Dictionary
model_version: "{{ version }}"
status: "{{ status }}"
template_version: 1
---

# Data Lineage and Data Dictionary — {{ version }}

## Source

- Source ID: `{{ source_id }}` ({{ source_name }})
- License: {{ license_url }}; intended use: {{ intended_use_short }}
- Retrieval date: {{ retrieval_date }}; source document: `{{ source_doc_path }}`

## Lineage chain

source `{{ source_id }}` → snapshot `{{ snapshot_id }}` (as-of {{ snapshot_as_of }}, checksum `{{ snapshot_checksum }}`) → training run `{{ training_run_id }}` → model version `{{ version }}`

## Data dictionary

| Source field | Normalised field | Type | Allowed range | Transformation | Feature use |
| --- | --- | --- | --- | --- | --- |
| loan_id | loan_id | string | pseudonymous hash | none | excluded (identifier) |
| as_of_date | as_of_date | date | 2022-01 .. | parsed to date | split/batch only |
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

{{ quality_summary }}

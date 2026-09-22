---
document_type: data_lineage
title: Data Lineage and Data Dictionary
model_version: pd-credit-v2.0.0
status: complete
template_version: 1
---

# Data Lineage and Data Dictionary — pd-credit-v2.0.0

## Source

- Source ID: `uci-credit-default-2005` (UCI 350 - Default of Credit Card Clients (Yeh & Lien, 2009))
- License: https://creativecommons.org/licenses/by/4.0/; intended use: Sharing and adaptation for any purpose with attribution. Citation: Yeh, I. (2009). Default of Credit Card Clients [Dataset]. UCI Machine Learning Repository. ht
- Retrieval date: 2026-09-22; source document: `docs/data-sources/uci-credit-default-2005.md`

## Lineage chain

source `uci-credit-default-2005` → snapshot `45392542-c9e2-4883-8d0c-a213c2efe8eb` (as-of 2005-09-30, checksum `30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933`) → training run `f677b88d-8b91-4d9f-b185-9a636612407d` → model version `pd-credit-v2.0.0`

## Data dictionary

| Source field | Normalised field | Type | Allowed range | Transformation | Feature use |
| --- | --- | --- | --- | --- | --- |
| ID | loan_id | string | pseudonymous hash | sha256(prefix:ID)[:12] | excluded (identifier) |
| — | as_of_date | date | 2005-09-30 (constant) | constant snapshot date | batch only; no temporal split |
| default payment next month | default_flag | boolean | {0,1} | none | target |
| LIMIT_BAL | credit_limit | numeric | 1,000 – 5,000,000 NT$ | median impute, standard scale | feature |
| BILL_AMT1 / LIMIT_BAL | utilization_recent | numeric | -5 – 10 | ratio, clipped | feature |
| mean(BILL_AMT1..6) / LIMIT_BAL | utilization_mean | numeric | -5 – 10 | ratio, clipped | feature |
| PAY_0 | pay_status_recent | integer | -2 – 9 | none | feature |
| max(PAY_0..PAY_6) | pay_status_max | integer | -2 – 9 | row max | feature |
| count(PAY_x > 0) | months_delinquent | integer | 0 – 6 | count of delinquent months | feature |
| mean(BILL_AMT1..6) | bill_amt_mean | numeric | NT$ | row mean | feature |
| mean(PAY_AMT1..6) | pay_amt_mean | numeric | NT$ | row mean | feature |
| sum(PAY_AMT) / sum(max(BILL_AMT, 0)) | pay_to_bill_ratio | numeric | 0 – 50 | ratio, clipped | feature |
| SEX | sex | categorical | male / female | code → label | excluded; fairness diagnostics only |
| AGE, EDUCATION, MARRIAGE | — | — | — | dropped | excluded by design (see rationale) |

## Quality results

- Status: **pass**; rows 30000; duplicate rate 0.00%; target rate 0.2212
- No issues raised.

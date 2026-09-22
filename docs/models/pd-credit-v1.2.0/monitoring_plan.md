---
document_type: monitoring_plan
title: Monitoring Plan
model_version: pd-credit-v1.2.0
status: draft
template_version: 1
owner: TODO
psi_bins: 10
alert_thresholds:
  psi_investigate: 0.1
  psi_alert: 0.25
  auc_drop: 0.05
  null_rate_max: 0.05
  duplicate_rate_max: 0.01
cadence: quarterly
---

# Monitoring Plan — pd-credit-v1.2.0

## Baseline distributions

Stored from the training cohort (train default rate 0.103): quantile bins for `annual_income`, `debt_to_income`, `loan_amount`, `interest_rate`, `term_months`, `credit_history_length`; level proportions for `employment_length`, `region`; score histogram mean 0.103.

## PSI configuration

10 quantile bins per numeric feature derived from the training cohort; categorical
features use level proportions; prediction scores use ten equal-width bins on [0, 1].

## Alert thresholds

Configurable project defaults, not regulatory thresholds: PSI < 0.1 stable,
0.1–0.25 investigate, > 0.25 alert. Holdout AUC drop
greater than 0.05 raises a performance alert when labels are available. Null rate above
5% or duplicate rate above 1% raises a data-quality alert.

## Owner and cadence

Owner: TODO. Cadence: TODO

## Escalation

TODO

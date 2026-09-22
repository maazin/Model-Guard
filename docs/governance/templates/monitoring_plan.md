---
document_type: monitoring_plan
title: Monitoring Plan
model_version: "{{ version }}"
status: "{{ status }}"
template_version: 1
owner: "{{ monitoring_owner }}"
psi_bins: {{ psi_bins }}
alert_thresholds:
  psi_investigate: {{ psi_investigate }}
  psi_alert: {{ psi_alert }}
  auc_drop: {{ auc_drop }}
  null_rate_max: 0.05
  duplicate_rate_max: 0.01
cadence: quarterly
---

# Monitoring Plan — {{ version }}

## Baseline distributions

{{ baseline_summary }}

## PSI configuration

{{ psi_bins }} quantile bins per numeric feature derived from the training cohort; categorical
features use level proportions; prediction scores use ten equal-width bins on [0, 1].

## Alert thresholds

Configurable project defaults, not regulatory thresholds: PSI < {{ psi_investigate }} stable,
{{ psi_investigate }}–{{ psi_alert }} investigate, > {{ psi_alert }} alert. Holdout AUC drop
greater than {{ auc_drop }} raises a performance alert when labels are available. Null rate above
5% or duplicate rate above 1% raises a data-quality alert.

## Owner and cadence

Owner: {{ monitoring_owner }}. Cadence: {{ cadence_text }}

## Escalation

{{ escalation }}

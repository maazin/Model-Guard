---
document_type: validation_report
title: Validation Report
model_version: "{{ version }}"
status: "{{ status }}"
template_version: 1
---

# Validation Report — {{ version }}

Each metric below states what was tested, the result, interpretation, limitation, the artifact
that holds the full output, and reviewer status.

## Scope

Holdout evaluation of the registered **{{ model_type }}** model against the logistic baseline on
the temporally later test partition ({{ split_test }} rows). Illustrative threshold
`{{ threshold }}` was chosen on the validation partition to maximise F1; it is **not** a lending
policy.

## Discrimination

{{ discrimination_table }}

## Calibration

{{ calibration_summary }}

## Threshold analysis

{{ threshold_summary }}

## Feature importance

{{ importance_table }}

## Hypothesis test

{{ hypothesis_summary }}

## Fairness diagnostics

{{ fairness_summary }}

## Limitations

{{ limitations }}

## Reviewer status

{{ reviewer_status }}

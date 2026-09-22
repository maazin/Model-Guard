---
document_type: risk_assessment
title: AI/Model Risk Assessment and Readiness Checklist
model_version: pd-credit-v1.1.0
status: complete
template_version: 1
fairness_unavailable_reason: null
---

# AI/Model Risk Assessment — pd-credit-v1.1.0

## Risk summary

Moderate model risk for a portfolio simulation: tabular supervised model with explainable features, temporal holdout, human approval gate, and quarterly drift monitoring. Key risks are population shift and over-interpretation of the illustrative threshold.

## Fairness assessment

Diagnostics computed on the synthetic `fairness_group` field (selection-rate ratio, TPR/FPR differences, group calibration). The field is never a model feature. Results are informational and not a legal determination.

## Readiness checklist

Readiness is evaluated live by the deterministic readiness engine; see the Governance page.

## Residual risk

Accepted for portfolio demonstration use only; any real deployment would require a licensed dataset, legal review and an independent validation.

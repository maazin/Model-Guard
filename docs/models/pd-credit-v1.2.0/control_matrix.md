---
document_type: control_matrix
title: Risk-Control Matrix
model_version: pd-credit-v1.2.0
status: draft
template_version: 1
---

# Risk-Control Matrix — pd-credit-v1.2.0

## Controls

| Control | Owner | Frequency | Status | Test evidence | Evidence URI |
| --- | --- | --- | --- | --- | --- |
| Data quality gate | data_scientist | per snapshot | tested | 8 unit tests | tests/unit/test_data_quality.py |
| Reproducible training | data_scientist | per run | tested | deterministic metrics test | tests/unit/test_training.py |

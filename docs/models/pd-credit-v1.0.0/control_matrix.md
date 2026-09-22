---
document_type: control_matrix
title: Risk-Control Matrix
model_version: pd-credit-v1.0.0
status: complete
template_version: 1
---

# Risk-Control Matrix — pd-credit-v1.0.0

## Controls

| Control | Owner | Frequency | Status | Test evidence | Evidence URI |
| --- | --- | --- | --- | --- | --- |
| Copilot data boundary | data_scientist | continuous | tested | prompt-injection and raw-row tests | tests/unit/test_copilot.py |
| Data quality gate | data_scientist | per snapshot | tested | 8 unit tests | tests/unit/test_data_quality.py |
| Hash-chained audit log | reviewer | continuous | tested | tamper detection tests | tests/unit/test_audit_chain.py |
| Human approval gate | reviewer | per version | tested | role enforcement tests | tests/integration/test_lifecycle_api.py |
| Monitoring and alerting | data_scientist | quarterly | implemented | drift alert integration test | apps/api/modelguard_api/services/monitoring.py |
| Reproducible training | data_scientist | per run | tested | deterministic metrics test | tests/unit/test_training.py |

---
document_type: model_card
title: Model Card
model_version: "{{ version }}"
model_uuid: "{{ model_uuid }}"
status: "{{ status }}"
template_version: 1
---

# Model Card — {{ version }}

## Model name and version

- Name: ModelGuard PD model (`{{ version }}`), immutable UUID `{{ model_uuid }}`
- Registered model type: **{{ model_type }}** ({{ model_algorithm }})
- Training run: `{{ training_run_id }}`; git SHA `{{ git_sha }}`
- Created: {{ created_at }}

## Business purpose and intended use

{{ business_purpose }}

## Out-of-scope uses

{{ out_of_scope }}

## Data source, license, and lineage

- Source: `{{ source_id }}` — {{ source_name }} (license: {{ license_url }}, retrieved {{ retrieval_date }})
- Snapshot as-of {{ snapshot_as_of }}, {{ row_count }} rows, SHA-256 `{{ snapshot_checksum }}`
- Lineage: source `{{ source_id }}` → snapshot `{{ snapshot_id }}` → training run `{{ training_run_id }}` → model version `{{ version }}`

## Target definition and modeling approach

{{ target_definition }}

Baseline: L2-regularised logistic regression. Champion candidate: scikit-learn
`HistGradientBoostingClassifier` (ADR-0002). Both share one preprocessing pipeline.

## Feature list and excluded-feature rationale

Features: {{ features }}

Excluded:
{{ excluded_rationale }}

## Training/validation split and reproducibility settings

- Split: {{ split_strategy }} (train {{ split_train }} / validation {{ split_validation }} / test {{ split_test }} rows)
- Random seed: `{{ seed }}`; training-data checksum `{{ snapshot_checksum }}`
- Hyperparameters: `{{ hyperparameters }}`
- Package versions: `{{ package_versions }}`

## Performance, calibration, and fairness results

{{ performance_summary }}

## Known limitations and failure modes

{{ limitations }}

## Monitoring plan and alert thresholds

{{ monitoring_summary }}

## Controls and owners

{{ controls_summary }}

## Approval state and change log

Approval state is maintained in the registry and audit log; see the change log document.
Current state at last render: **{{ state }}**.

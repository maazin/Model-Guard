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

{{ data_dictionary }}

## Quality results

{{ quality_summary }}

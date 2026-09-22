# data/sources

Place **licensed** raw dataset files here before importing them with `POST /api/v1/snapshots/import`.
This directory is git-ignored. Before adding a file:

1. Read the dataset's license and terms of use yourself.
2. Register the source (`POST /api/v1/data-sources`) — this writes `docs/data-sources/<source_id>.md`
   with the license URL, allowed use, retrieval date and limitations, and records who confirmed the license
   in the audit log.
3. If the source schema differs from the ModelGuard schema, add a `ColumnMapAdapter` in
   `packages/ml/modelguard_ml/adapters.py` and document each transformation in the data dictionary.

Nothing is downloaded automatically. See ADR-0001.

## Included file

`uci-credit-default-2005/default of credit card clients.xls` — UCI 350, CC BY 4.0. Yeh, I. (2009). Default of Credit Card Clients [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H. Committed so that Docker, CI and hosted deployments build the real-data model version; monitoring batches are regenerated from it by the seed.

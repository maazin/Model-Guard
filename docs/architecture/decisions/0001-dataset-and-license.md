# ADR-0001: Dataset and license

**Status:** Accepted (2026-09-22). Dataset: **UCI 350 — Default of Credit Card Clients**, CC BY 4.0, license
acceptability confirmed by the repository owner after reading the UCI listing.

## Context

The PRD requires "one properly licensed, publicly accessible loan-performance or consumer-credit dataset" and forbids
inventing license facts or downloading data without a human confirming the license.

## Decision

1. **Licensed public dataset:** UCI 350 (Yeh & Lien, 2009), 30,000 rows, binary next-month default target. The UCI
   listing states the dataset is CC BY 4.0 ("sharing and adaptation for any purpose, provided that the appropriate
   credit is given"). Attribution is given in `docs/data-sources/uci-credit-default-2005.md`, the README, and every
   model card rendered for `pd-credit-v2.x`. The raw file lives under `data/sources/` (git-ignored); `make fetch-uci`
   prints the terms and requires an explicit "y" before downloading.
2. **Synthetic fixture stays:** `data/fixtures/synthetic_loans.csv` (MIT, in-repo) drives every test, CI and the
   `pd-credit-v1.x` demo versions, so the project remains fully offline-reproducible without the real file.
3. **Per-source feature spec:** a `FeatureSpec` (`packages/ml/modelguard_ml/spec.py`) declares each source's
   features, ranges, exclusions, fairness field and whether `as_of_date` is a valid time axis. The UCI adapter
   engineers utilisation, repayment-status and payment-ratio features and never maps unrelated columns onto the
   synthetic loan schema.

## Alternatives considered (license pages read 2026-09-22)

| Candidate | Terms observed | Why not |
| --- | --- | --- |
| UCI Statlog German Credit | CC BY 4.0 | 1,000 rows — too small for bootstrap CIs and monitoring batches |
| Freddie Mac Single-Family Loan-Level | Free for non-commercial/academic use subject to a Terms & Conditions PDF; registration on Clarity required; separate licence for commercial redistribution | Gigabytes of mortgage data behind a sign-in; T&Cs would need review before any sample could be kept; deferred as a stretch goal (its monthly time axis would enable a real temporal split) |

## Consequences

- UCI 350 has no time axis, so `pd-credit-v2.x` uses the documented stratified fallback (ADR-0003).
- Demographic fields (`SEX`, `AGE`, `EDUCATION`, `MARRIAGE`) are excluded from features (ADR-0004); `sex` is used
  only for fairness diagnostics.
- Monitoring batches for the UCI source are generated stress scenarios (`scripts/generate_uci_batches.py`), stated
  as such in the source document and monitoring plan.

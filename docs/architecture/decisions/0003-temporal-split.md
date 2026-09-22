# ADR-0003: Temporal split

**Status:** Accepted

## Decision

`modelguard_ml.splits.temporal_split` orders rows by `as_of_date` and cuts at the 60% / 80% row quantiles: train on the earliest 60%, validate on the next 20%, test (holdout) on the latest 20%. Rows on a boundary date go to the later partition.

## Rationale

A PD model is used on future cohorts, so the honest estimate of generalisation is out-of-time. A stratified random split would leak period effects and overstate performance.

## Limitation (documented in every validation report)

The fixture covers 24 months of synthetic originations with no macro regime change, so the temporal holdout still under-represents real-world drift. Bootstrap confidence intervals are computed on the holdout only and do not capture period-to-period variance. If a chosen public dataset has no valid time field, the split must fall back to stratified sampling and this limitation must be restated in the model card.

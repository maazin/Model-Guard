"""Temporal train/validation/test split with a documented stratified fallback (ADR-0003)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass
class SplitResult:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    strategy: str
    boundaries: dict[str, str]

    def counts(self) -> dict[str, int]:
        return {"train": len(self.train), "validation": len(self.validation), "test": len(self.test)}


def temporal_split(df: pd.DataFrame, train_frac: float = 0.6, valid_frac: float = 0.2) -> SplitResult:
    """Order by as_of_date and cut by row quantile so the holdout is strictly later in time.

    Rows sharing a boundary date all go to the later bucket, which keeps the split leak-free
    at the cost of slightly uneven fractions.
    """
    if "as_of_date" not in df.columns:
        raise ValueError("temporal split requires as_of_date")
    d = df.copy()
    d["as_of_date"] = pd.to_datetime(d["as_of_date"])
    d = d.sort_values(["as_of_date", "loan_id"], kind="mergesort").reset_index(drop=True)
    n = len(d)
    t_cut = d["as_of_date"].iloc[int(n * train_frac)]
    v_cut = d["as_of_date"].iloc[int(n * (train_frac + valid_frac))]
    train = d[d["as_of_date"] < t_cut]
    valid = d[(d["as_of_date"] >= t_cut) & (d["as_of_date"] < v_cut)]
    test = d[d["as_of_date"] >= v_cut]
    if len(train) == 0 or len(valid) == 0 or len(test) == 0:
        raise ValueError("temporal split produced an empty partition; check date coverage")
    return SplitResult(
        train,
        valid,
        test,
        "temporal",
        {"train_end": str(t_cut.date()), "validation_end": str(v_cut.date())},
    )


def stratified_split(df: pd.DataFrame, seed: int, train_frac: float = 0.6, valid_frac: float = 0.2) -> SplitResult:
    """Fallback when the source has no valid time axis. Stratified on the target; limitation documented."""
    rest_frac = 1 - train_frac
    train, rest = train_test_split(df, test_size=rest_frac, stratify=df["default_flag"], random_state=seed)
    valid, test = train_test_split(
        rest, test_size=1 - valid_frac / rest_frac, stratify=rest["default_flag"], random_state=seed
    )
    return SplitResult(
        train.reset_index(drop=True),
        valid.reset_index(drop=True),
        test.reset_index(drop=True),
        "stratified",
        {"note": "no valid time field; stratified random split, so no out-of-time estimate"},
    )


def choose_split(df: pd.DataFrame, seed: int, time_field_valid: bool) -> SplitResult:
    """Temporal when the source declares a valid time axis with enough distinct dates, else stratified."""
    if time_field_valid and "as_of_date" in df.columns and df["as_of_date"].nunique() >= 3:
        return temporal_split(df)
    return stratified_split(df, seed)

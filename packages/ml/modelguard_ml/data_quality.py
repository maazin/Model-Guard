"""Schema, null-rate, range, duplicate and target checks for snapshots and monitoring batches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from modelguard_shared.constants import (
    ALLOWED_RANGES,
    CATEGORICAL_FEATURES,
    EMPLOYMENT_LENGTH_LEVELS,
    NUMERIC_FEATURES,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
)


@dataclass
class QualityIssue:
    check: str
    severity: str  # "error" | "warning"
    detail: str
    field: str | None = None


@dataclass
class QualityReport:
    status: str  # "pass" | "warn" | "fail"
    row_count: int
    duplicate_rate: float
    null_rates: dict[str, float]
    target_rate: float | None
    target_available: bool
    issues: list[QualityIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "row_count": self.row_count,
            "duplicate_rate": self.duplicate_rate,
            "null_rates": self.null_rates,
            "target_rate": self.target_rate,
            "target_available": self.target_available,
            "issues": [i.__dict__ for i in self.issues],
        }


def check_schema(df: pd.DataFrame, require_target: bool = True) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    required = [c for c in REQUIRED_COLUMNS if require_target or c != "default_flag"]
    for col in required:
        if col not in df.columns:
            issues.append(QualityIssue("schema", "error", f"missing required column '{col}'", col))
    unknown = [c for c in df.columns if c not in REQUIRED_COLUMNS + OPTIONAL_COLUMNS]
    if unknown:
        issues.append(QualityIssue("schema", "warning", f"unexpected columns ignored: {unknown}"))
    return issues


def run_quality_checks(
    df: pd.DataFrame,
    *,
    require_target: bool = True,
    max_null_rate: float = 0.05,
    max_duplicate_rate: float = 0.01,
) -> QualityReport:
    issues = check_schema(df, require_target=require_target)
    if any(i.severity == "error" for i in issues):
        return QualityReport("fail", len(df), 0.0, {}, None, False, issues)

    null_rates = {c: float(df[c].isna().mean()) for c in df.columns}
    for col, rate in null_rates.items():
        if col in NUMERIC_FEATURES + CATEGORICAL_FEATURES and rate > max_null_rate:
            issues.append(
                QualityIssue("null_rate", "error", f"null rate {rate:.2%} exceeds {max_null_rate:.0%}", col)
            )
    dup_rate = float(df.duplicated(subset=["loan_id"]).mean()) if len(df) else 0.0
    if dup_rate > max_duplicate_rate:
        issues.append(
            QualityIssue("duplicates", "error", f"duplicate loan_id rate {dup_rate:.2%} exceeds {max_duplicate_rate:.0%}")
        )

    for col, (lo, hi) in ALLOWED_RANGES.items():
        if col not in df.columns:
            continue
        vals = pd.to_numeric(df[col], errors="coerce")
        out = ((vals < lo) | (vals > hi)).sum()
        if out:
            issues.append(
                QualityIssue("range", "error", f"{int(out)} values outside allowed range [{lo}, {hi}]", col)
            )
    if "employment_length" in df.columns:
        bad = set(df["employment_length"].dropna().astype(str)) - set(EMPLOYMENT_LENGTH_LEVELS)
        if bad:
            issues.append(QualityIssue("range", "error", f"unknown employment_length levels: {sorted(bad)}", "employment_length"))

    target_available = "default_flag" in df.columns and df["default_flag"].notna().any()
    target_rate: float | None = None
    if target_available:
        t = pd.to_numeric(df["default_flag"], errors="coerce")
        if not np.isin(t.dropna().unique(), [0, 1]).all():
            issues.append(QualityIssue("target", "error", "default_flag must be 0/1", "default_flag"))
        else:
            target_rate = float(t.mean())
            if target_rate in (0.0, 1.0):
                issues.append(QualityIssue("target", "error", "target has a single class", "default_flag"))
    elif require_target:
        issues.append(QualityIssue("target", "error", "target default_flag unavailable", "default_flag"))
    else:
        issues.append(QualityIssue("target", "warning", "labels unavailable; performance metrics skipped"))

    if any(i.severity == "error" for i in issues):
        status = "fail"
    elif issues:
        status = "warn"
    else:
        status = "pass"
    return QualityReport(status, len(df), dup_rate, null_rates, target_rate, target_available, issues)


def profile(df: pd.DataFrame) -> dict[str, Any]:
    """Descriptive statistics per numeric feature plus target distribution; never row-level data."""
    out: dict[str, Any] = {"numeric": {}, "categorical": {}, "row_count": int(len(df))}
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            out["numeric"][col] = {
                "mean": float(s.mean()),
                "std": float(s.std()),
                "min": float(s.min()),
                "p25": float(s.quantile(0.25)),
                "median": float(s.median()),
                "p75": float(s.quantile(0.75)),
                "max": float(s.max()),
                "null_rate": float(s.isna().mean()),
            }
    for col in CATEGORICAL_FEATURES + ("region", "fairness_group"):
        if col in df.columns:
            out["categorical"][col] = {str(k): int(v) for k, v in df[col].astype(str).value_counts().items()}
    if "default_flag" in df.columns:
        t = pd.to_numeric(df["default_flag"], errors="coerce")
        out["target"] = {"positive": int(t.sum()), "negative": int((t == 0).sum()), "rate": float(t.mean())}
    return out

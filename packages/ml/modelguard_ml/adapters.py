"""Pluggable dataset adapters (ADR-0001).

An adapter turns a source file into the normalised ModelGuard schema and carries the source's
`FeatureSpec`. The synthetic fixture is already normalised; the UCI "Default of Credit Card
Clients" adapter engineers documented features from the raw payment history. Adapters never
download anything: the file must already be under `data/`.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
import pandas as pd

from modelguard_ml.spec import SYNTHETIC_SPEC, DictionaryRow, FeatureSpec


class DatasetAdapter(Protocol):
    source_id: str
    spec: FeatureSpec

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame: ...


def pseudonymous_id(prefix: str, value: object) -> str:
    return "ln_" + hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:12]


@dataclass
class PassthroughAdapter:
    """For files already in the normalised schema (the synthetic fixture)."""

    source_id: str = "synthetic-loans-v1"
    spec: FeatureSpec = SYNTHETIC_SPEC

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        keep = [c for c in self.spec.required_columns + self.spec.optional_columns if c in raw.columns]
        return raw[keep].copy()


@dataclass
class ColumnMapAdapter:
    """Rename source columns and apply documented transformations."""

    source_id: str
    mapping: dict[str, str]
    spec: FeatureSpec
    transforms: dict[str, Callable[[pd.Series], pd.Series]] = field(default_factory=dict)

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        missing = [src for src in self.mapping.values() if src not in raw.columns]
        if missing:
            raise ValueError(f"source columns missing for adapter {self.source_id}: {missing}")
        out = pd.DataFrame({norm: raw[src] for norm, src in self.mapping.items()})
        for col, fn in self.transforms.items():
            out[col] = fn(out[col])
        return out


# ---------------------------------------------------------------------------
# UCI 350 - Default of Credit Card Clients (Yeh & Lien, 2009), CC BY 4.0
# ---------------------------------------------------------------------------

UCI_SOURCE_ID = "uci-credit-default-2005"
_PAY = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
_BILL = [f"BILL_AMT{i}" for i in range(1, 7)]
_PAID = [f"PAY_AMT{i}" for i in range(1, 7)]

UCI_SPEC = FeatureSpec(
    source_id=UCI_SOURCE_ID,
    numeric=(
        "credit_limit",
        "utilization_recent",
        "utilization_mean",
        "pay_status_recent",
        "pay_status_max",
        "months_delinquent",
        "bill_amt_mean",
        "pay_amt_mean",
        "pay_to_bill_ratio",
    ),
    categorical={},
    ranges={
        "credit_limit": (1_000.0, 5_000_000.0),
        "utilization_recent": (-5.0, 10.0),
        "utilization_mean": (-5.0, 10.0),
        "pay_status_recent": (-2.0, 9.0),
        "pay_status_max": (-2.0, 9.0),
        "months_delinquent": (0.0, 6.0),
        "bill_amt_mean": (-1_000_000.0, 5_000_000.0),
        "pay_amt_mean": (0.0, 5_000_000.0),
        "pay_to_bill_ratio": (0.0, 50.0),
    },
    excluded={
        "loan_id": "Pseudonymous hash of the source ID; identifiers carry no predictive meaning.",
        "as_of_date": "Constant (September 2005 snapshot); used only for batch assignment.",
        "sex": "Protected characteristic; retained solely for fairness diagnostics, never a feature.",
        "age": "Protected/age-related characteristic; excluded from features by design.",
        "education": "Socio-economic proxy with unclear coding (levels 0, 5, 6 undocumented); excluded.",
        "marriage": "Protected/family-status proxy; excluded from features by design.",
    },
    fairness_field="sex",
    monitoring_only=(),
    time_field_valid=False,
    target_definition=(
        "`default_flag` = source variable `default payment next month` (1 = the cardholder defaulted on the "
        "October 2005 payment). Leakage controls: only April–September 2005 history is used; no post-outcome fields exist."
    ),
    dictionary=(
        DictionaryRow(
            "ID", "loan_id", "string", "pseudonymous hash", "sha256(prefix:ID)[:12]", "excluded (identifier)"
        ),
        DictionaryRow(
            "—",
            "as_of_date",
            "date",
            "2005-09-30 (constant)",
            "constant snapshot date",
            "batch only; no temporal split",
        ),
        DictionaryRow("default payment next month", "default_flag", "boolean", "{0,1}", "none", "target"),
        DictionaryRow(
            "LIMIT_BAL", "credit_limit", "numeric", "1,000 – 5,000,000 NT$", "median impute, standard scale", "feature"
        ),
        DictionaryRow("BILL_AMT1 / LIMIT_BAL", "utilization_recent", "numeric", "-5 – 10", "ratio, clipped", "feature"),
        DictionaryRow(
            "mean(BILL_AMT1..6) / LIMIT_BAL", "utilization_mean", "numeric", "-5 – 10", "ratio, clipped", "feature"
        ),
        DictionaryRow("PAY_0", "pay_status_recent", "integer", "-2 – 9", "none", "feature"),
        DictionaryRow("max(PAY_0..PAY_6)", "pay_status_max", "integer", "-2 – 9", "row max", "feature"),
        DictionaryRow(
            "count(PAY_x > 0)", "months_delinquent", "integer", "0 – 6", "count of delinquent months", "feature"
        ),
        DictionaryRow("mean(BILL_AMT1..6)", "bill_amt_mean", "numeric", "NT$", "row mean", "feature"),
        DictionaryRow("mean(PAY_AMT1..6)", "pay_amt_mean", "numeric", "NT$", "row mean", "feature"),
        DictionaryRow(
            "sum(PAY_AMT) / sum(max(BILL_AMT, 0))",
            "pay_to_bill_ratio",
            "numeric",
            "0 – 50",
            "ratio, clipped",
            "feature",
        ),
        DictionaryRow(
            "SEX", "sex", "categorical", "male / female", "code → label", "excluded; fairness diagnostics only"
        ),
        DictionaryRow("AGE, EDUCATION, MARRIAGE", "—", "—", "—", "dropped", "excluded by design (see rationale)"),
    ),
)


@dataclass
class UciCreditDefaultAdapter:
    """Engineers ModelGuard features from the raw UCI 350 sheet (header row 1 of the .xls)."""

    source_id: str = UCI_SOURCE_ID
    spec: FeatureSpec = UCI_SPEC
    as_of_date: str = "2005-09-30"

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = raw.copy()
        if "default payment next month" not in df.columns and "Y" in df.columns:
            df = df.rename(columns={"Y": "default payment next month"})
        needed = ["ID", "LIMIT_BAL", "SEX", "default payment next month", *_PAY, *_BILL, *_PAID]
        missing = [c for c in needed if c not in df.columns]
        if missing:
            raise ValueError(f"UCI adapter: source columns missing: {missing}")
        limit = df["LIMIT_BAL"].astype(float).clip(lower=1.0)
        bills = df[_BILL].astype(float)
        paid = df[_PAID].astype(float)
        pays = df[_PAY].astype(float)
        out = pd.DataFrame(
            {
                "loan_id": [pseudonymous_id(self.source_id, v) for v in df["ID"]],
                "as_of_date": self.as_of_date,
                "default_flag": df["default payment next month"].astype(int),
                "credit_limit": limit,
                "utilization_recent": (bills["BILL_AMT1"] / limit).clip(-5, 10),
                "utilization_mean": (bills.mean(axis=1) / limit).clip(-5, 10),
                "pay_status_recent": pays["PAY_0"],
                "pay_status_max": pays.max(axis=1),
                "months_delinquent": (pays > 0).sum(axis=1).astype(float),
                "bill_amt_mean": bills.mean(axis=1),
                "pay_amt_mean": paid.mean(axis=1),
                "pay_to_bill_ratio": (paid.sum(axis=1) / np.maximum(bills.clip(lower=0).sum(axis=1), 1.0)).clip(0, 50),
                "sex": df["SEX"].map({1: "male", 2: "female"}).fillna("unknown"),
            }
        )
        return out


ADAPTERS: dict[str, DatasetAdapter] = {
    "synthetic-loans-v1": PassthroughAdapter(),
    UCI_SOURCE_ID: UciCreditDefaultAdapter(),
}


def get_adapter(source_id: str) -> DatasetAdapter:
    return ADAPTERS.get(source_id, PassthroughAdapter(source_id))


def get_spec(source_id: str) -> FeatureSpec:
    return get_adapter(source_id).spec

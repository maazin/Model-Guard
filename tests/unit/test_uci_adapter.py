"""UCI 350 adapter, per-source FeatureSpec, and the stratified split fallback (no raw file needed)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from modelguard_ml.adapters import UCI_SPEC, UciCreditDefaultAdapter, get_adapter, get_spec
from modelguard_ml.data_quality import run_quality_checks
from modelguard_ml.spec import SYNTHETIC_SPEC, FeatureSpec
from modelguard_ml.splits import choose_split
from modelguard_ml.training import train_models


def fake_uci(n: int = 600, seed: int = 3) -> pd.DataFrame:
    """Raw frame in the UCI column layout with a payment-history-driven default process."""
    rng = np.random.default_rng(seed)
    pay = rng.integers(-2, 4, size=(n, 6))
    limit = rng.choice([20_000, 50_000, 100_000, 200_000], size=n)
    bills = rng.uniform(0, 1, size=(n, 6)) * limit[:, None]
    paid = rng.uniform(0, 0.3, size=(n, 6)) * bills
    logit = -2.0 + 0.6 * pay.max(axis=1) + 0.5 * (bills[:, 0] / limit)
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-logit))).astype(int)
    df = pd.DataFrame(
        {
            "ID": np.arange(1, n + 1),
            "LIMIT_BAL": limit,
            "SEX": rng.integers(1, 3, n),
            "EDUCATION": 2,
            "MARRIAGE": 1,
            "AGE": 35,
        }
    )
    for i, col in enumerate(["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]):
        df[col] = pay[:, i]
    for i in range(6):
        df[f"BILL_AMT{i + 1}"] = bills[:, i].round()
        df[f"PAY_AMT{i + 1}"] = paid[:, i].round()
    df["default payment next month"] = y
    return df


def test_adapter_normalises_and_passes_quality_checks():
    raw = fake_uci()
    df = UciCreditDefaultAdapter().normalize(raw)
    assert set(UCI_SPEC.required_columns) <= set(df.columns) and "sex" in df.columns
    assert df["loan_id"].str.match(r"^ln_[0-9a-f]{12}$").all() and df["loan_id"].is_unique
    assert not {"AGE", "EDUCATION", "MARRIAGE", "SEX"} & set(df.columns)  # excluded raw fields never leak
    assert df["months_delinquent"].between(0, 6).all() and df["pay_status_max"].max() <= 9
    report = run_quality_checks(df, spec=UCI_SPEC)
    assert report.status == "pass", report.issues
    with pytest.raises(ValueError):
        UciCreditDefaultAdapter().normalize(raw.drop(columns=["PAY_AMT3"]))


def test_spec_round_trip_and_registry():
    d = UCI_SPEC.to_dict()
    assert FeatureSpec.from_dict(d) == UCI_SPEC
    assert get_spec("uci-credit-default-2005") is UCI_SPEC and get_spec("synthetic-loans-v1") is SYNTHETIC_SPEC
    assert get_adapter("unknown-source").spec is SYNTHETIC_SPEC
    assert "| SEX | sex |" in UCI_SPEC.dictionary_markdown()


def test_stratified_fallback_when_no_time_axis():
    df = UciCreditDefaultAdapter().normalize(fake_uci())
    s = choose_split(df, seed=1, time_field_valid=UCI_SPEC.time_field_valid)
    assert s.strategy == "stratified" and sum(s.counts().values()) == len(df)
    rates = [part["default_flag"].mean() for part in (s.train, s.validation, s.test)]
    assert max(rates) - min(rates) < 0.05


def test_training_uses_the_source_spec_end_to_end():
    df = UciCreditDefaultAdapter().normalize(fake_uci(n=900))
    r = train_models(df, seed=5, data_checksum="uci", n_bootstrap=20, spec=UCI_SPEC)
    assert r.config["split"]["strategy"] == "stratified"
    assert (
        r.config["features"] == list(UCI_SPEC.features) and r.config["feature_spec"]["source_id"] == UCI_SPEC.source_id
    )
    assert set(r.baseline_distributions["numeric"]) == set(UCI_SPEC.numeric)
    assert r.evaluations["champion"].fairness is not None and set(r.evaluations["champion"].fairness["groups"]) <= {
        "male",
        "female",
    }
    assert r.hypothesis_tests[0]["feature"] == "credit_limit"
    assert r.evaluations["champion"].metrics["auc"]["value"] > 0.6

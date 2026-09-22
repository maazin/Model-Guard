import numpy as np
import pandas as pd
import pytest
from modelguard_ml.data_quality import profile, run_quality_checks
from modelguard_ml.synthetic import generate_loans
from modelguard_shared.hashing import sha256_file, sha256_text


@pytest.fixture
def df():
    return generate_loans(n=300, seed=1)


def test_clean_fixture_passes(df):
    r = run_quality_checks(df)
    assert r.status == "pass" and r.target_available and 0 < r.target_rate < 1


def test_missing_schema_field_fails(df):
    r = run_quality_checks(df.drop(columns=["debt_to_income"]))
    assert r.status == "fail"
    assert any(i.check == "schema" and i.field == "debt_to_income" for i in r.issues)


def test_bad_range_fails(df):
    df.loc[0, "interest_rate"] = 99.0
    r = run_quality_checks(df)
    assert any(i.check == "range" and i.field == "interest_rate" for i in r.issues)


def test_duplicate_rows_fail(df):
    dup = pd.concat([df, df.head(20)], ignore_index=True)
    r = run_quality_checks(dup)
    assert r.status == "fail" and any(i.check == "duplicates" for i in r.issues)


def test_invalid_target_fails(df):
    df["default_flag"] = 2
    r = run_quality_checks(df)
    assert any(i.check == "target" for i in r.issues)


def test_missing_target_is_warning_when_not_required(df):
    r = run_quality_checks(df.drop(columns=["default_flag"]), require_target=False)
    assert r.status == "warn" and not r.target_available


def test_high_null_rate_fails(df):
    df.loc[: len(df) // 2, "annual_income"] = np.nan
    r = run_quality_checks(df)
    assert any(i.check == "null_rate" for i in r.issues)


def test_checksum_changes_when_file_changes(tmp_path, df):
    p = tmp_path / "a.csv"
    df.to_csv(p, index=False)
    before = sha256_file(p)
    df.loc[0, "loan_amount"] += 1
    df.to_csv(p, index=False)
    assert sha256_file(p) != before
    assert sha256_text("a") != sha256_text("b")


def test_profile_has_no_row_level_data(df):
    p = profile(df)
    assert "numeric" in p and "target" in p
    assert not any("ln_" in str(v) for v in p.values())


def test_column_map_adapter_normalises_and_validates():
    from modelguard_ml.adapters import ColumnMapAdapter, get_adapter

    raw = pd.DataFrame(
        {
            "id": ["a", "b"],
            "dt": ["2024-01-31", "2024-02-29"],
            "bad": [0, 1],
            "inc": [50_000, 60_000],
            "dti_pct": [20, 30],
        }
    )
    adapter = ColumnMapAdapter(
        "example",
        {
            "loan_id": "id",
            "as_of_date": "dt",
            "default_flag": "bad",
            "annual_income": "inc",
            "debt_to_income": "dti_pct",
        },
        {"debt_to_income": lambda s: s.astype(float)},
    )
    out = adapter.normalize(raw)
    assert list(out.columns) == ["loan_id", "as_of_date", "default_flag", "annual_income", "debt_to_income"]
    with pytest.raises(ValueError):
        ColumnMapAdapter("x", {"loan_id": "nope"}).normalize(raw)
    assert get_adapter("synthetic-loans-v1").normalize(generate_loans(n=5, seed=1)).shape[0] == 5

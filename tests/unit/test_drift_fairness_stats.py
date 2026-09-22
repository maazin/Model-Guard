import numpy as np
import pandas as pd
import pytest

from modelguard_ml import drift
from modelguard_ml.fairness import group_metrics
from modelguard_ml.stats_tests import two_sample_ks


def test_psi_identical_distribution_is_zero():
    assert drift.psi_from_distributions(np.array([10, 20, 30]), np.array([10, 20, 30])) == pytest.approx(0.0)


def test_psi_known_value():
    e = np.array([0.5, 0.5])
    a = np.array([0.7, 0.3])
    expected = (0.7 - 0.5) * np.log(0.7 / 0.5) + (0.3 - 0.5) * np.log(0.3 / 0.5)
    assert drift.psi_from_distributions(e, a) == pytest.approx(expected, abs=1e-6)


def test_numeric_psi_detects_shift():
    rng = np.random.default_rng(0)
    base = rng.normal(0, 1, 5000)
    same = rng.normal(0, 1, 5000)
    shifted = rng.normal(1.2, 1, 5000)
    assert drift.numeric_psi(base, same)["status"] == "stable"
    assert drift.numeric_psi(base, shifted)["status"] == "alert"


def test_categorical_psi_with_new_level():
    b = pd.Series(["a"] * 50 + ["b"] * 50)
    c = pd.Series(["a"] * 50 + ["c"] * 50)
    r = drift.categorical_psi(b, c)
    assert r["psi"] > drift.PSI_ALERT and "c" in r["bins"]


def test_psi_status_thresholds():
    assert drift.psi_status(0.05) == "stable"
    assert drift.psi_status(0.15) == "investigate"
    assert drift.psi_status(0.30) == "alert"


def test_score_drift_reports_mean_shift():
    r = drift.score_drift(np.full(100, 0.1), np.full(100, 0.4))
    assert r["mean_shift"] == pytest.approx(0.3)


def test_fairness_metrics_symmetry():
    y = np.array([1, 0, 1, 0] * 25)
    p = np.array([0.9, 0.1, 0.9, 0.1] * 25)
    g = np.array(["A", "A", "B", "B"] * 25)
    r = group_metrics(y, p, g, 0.5)
    assert r["selection_rate_ratio"] == pytest.approx(1.0)
    assert r["tpr_difference"] == pytest.approx(0.0)
    assert r["fpr_difference"] == pytest.approx(0.0)
    assert set(r["groups"]) == {"A", "B"}


def test_fairness_detects_selection_gap():
    y = np.array([0, 0] * 50)
    p = np.array([0.9, 0.1] * 50)
    g = np.array(["A", "B"] * 50)
    r = group_metrics(y, p, g, 0.5)
    assert r["selection_rate_ratio"] == pytest.approx(0.0)
    assert r["fpr_difference"] == pytest.approx(1.0)


def test_two_sample_ks_reports_fields():
    rng = np.random.default_rng(3)
    r = two_sample_ks(rng.normal(0, 1, 500), rng.normal(0.8, 1, 500), "x")
    assert r["reject_null"] is True and r["p_value"] < 0.05
    assert r["effect_size"]["cohens_d"] == pytest.approx(0.8, abs=0.25)
    assert "limitation" in r and r["assumptions"]

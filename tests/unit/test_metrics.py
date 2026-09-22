import numpy as np
import pytest
from modelguard_ml import metrics as M
from sklearn.metrics import brier_score_loss, roc_auc_score


@pytest.fixture
def sample():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    s = np.clip(rng.normal(0.3 + 0.4 * y, 0.2), 0, 1)
    return y, s


def test_auc_matches_sklearn(sample):
    y, s = sample
    assert M.auc_roc(y, s) == pytest.approx(roc_auc_score(y, s), abs=1e-9)


def test_auc_perfect_and_random():
    y = np.array([0, 0, 1, 1])
    assert M.auc_roc(y, np.array([0.1, 0.2, 0.8, 0.9])) == 1.0
    assert M.auc_roc(y, np.array([0.9, 0.8, 0.2, 0.1])) == 0.0
    assert M.auc_roc(y, np.array([0.5, 0.5, 0.5, 0.5])) == pytest.approx(0.5)


def test_auc_single_class_raises():
    with pytest.raises(ValueError):
        M.auc_roc(np.zeros(5), np.linspace(0, 1, 5))


def test_ks_is_max_tpr_minus_fpr(sample):
    y, s = sample
    fpr, tpr, _ = M.roc_curve_points(y, s)
    assert M.ks_statistic(y, s) == pytest.approx(np.max(tpr - fpr))
    assert 0 <= M.ks_statistic(y, s) <= 1
    assert M.ks_statistic(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.8, 0.9])) == 1.0


def test_brier_matches_sklearn(sample):
    y, s = sample
    assert M.brier_score(y, s) == pytest.approx(brier_score_loss(y, s))


def test_calibration_perfectly_calibrated_has_low_ece():
    rng = np.random.default_rng(1)
    p = rng.uniform(size=20000)
    y = (rng.uniform(size=20000) < p).astype(int)
    cal = M.calibration(y, p, n_bins=10)
    assert cal.ece < 0.02
    assert len(cal.bin_count) == 10 and sum(cal.bin_count) == 20000


def test_calibration_edge_probabilities_do_not_overflow_bins():
    cal = M.calibration(np.array([0, 1, 1, 0]), np.array([0.0, 1.0, 1.0, 0.0]), n_bins=5)
    assert sum(cal.bin_count) == 4


def test_ece_known_value():
    # two bins: predicted 0.2 with observed 0.5 -> |0.3|; predicted 0.8 with observed 1.0 -> 0.2
    y = np.array([0, 1, 1, 1])
    p = np.array([0.2, 0.2, 0.8, 0.8])
    assert M.expected_calibration_error(y, p, n_bins=2) == pytest.approx(0.5 * 0.3 + 0.5 * 0.2)


def test_confusion_matrix_counts():
    y = np.array([1, 1, 0, 0, 1])
    p = np.array([0.9, 0.4, 0.6, 0.1, 0.7])
    c = M.confusion_at_threshold(y, p, 0.5)
    assert (c.tp, c.fp, c.tn, c.fn) == (2, 1, 1, 1)
    assert c.precision == pytest.approx(2 / 3)
    assert c.recall == pytest.approx(2 / 3)


def test_threshold_analysis_grid(sample):
    y, s = sample
    rows = M.threshold_analysis(y, s)
    assert len(rows) == 19
    # selection rate must be monotonically non-increasing with threshold
    rates = [r["selection_rate"] for r in rows]
    assert all(a >= b for a, b in zip(rates[:-1], rates[1:], strict=True))


def test_bootstrap_ci_contains_point_and_is_deterministic(sample):
    y, s = sample
    a = M.bootstrap_ci(y, s, M.auc_roc, n_bootstrap=200, seed=7)
    b = M.bootstrap_ci(y, s, M.auc_roc, n_bootstrap=200, seed=7)
    assert a.lower <= a.point <= a.upper
    assert (a.lower, a.upper) == (b.lower, b.upper)
    assert a.n_bootstrap == 200

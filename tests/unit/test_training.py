import pandas as pd
import pytest
from modelguard_ml.splits import temporal_split
from modelguard_ml.synthetic import generate_loans
from modelguard_ml.training import load_pipeline, save_artifacts, train_models


@pytest.fixture(scope="module")
def df():
    return generate_loans(n=1500, seed=5)


def test_temporal_split_is_ordered(df):
    s = temporal_split(df)
    assert pd.to_datetime(s.train.as_of_date).max() < pd.to_datetime(s.test.as_of_date).min()
    assert sum(s.counts().values()) == len(df)


def test_training_is_deterministic_and_reproducible(df, tmp_path):
    a = train_models(df, seed=11, data_checksum="abc", n_bootstrap=30)
    b = train_models(df, seed=11, data_checksum="abc", n_bootstrap=30)
    assert a.metrics_summary() == b.metrics_summary()
    assert a.config["random_seed"] == 11 and a.config["training_data_checksum"] == "abc"
    for mt in ("baseline", "champion"):
        m = a.evaluations[mt].metrics
        assert 0.5 < m["auc"]["value"] < 1.0
        assert m["auc"]["lower_ci"] <= m["auc"]["value"] <= m["auc"]["upper_ci"]
        assert a.evaluations[mt].feature_importance
        assert a.evaluations[mt].fairness is not None
    paths = save_artifacts(a, tmp_path)
    pipe = load_pipeline(paths["champion_model"])
    X = df[a.config["features"]].head(5)
    assert pipe.predict_proba(X).shape == (5, 2)
    assert a.hypothesis_tests[0]["test"] == "two_sample_ks"
    assert "annual_income" in a.baseline_distributions["numeric"]

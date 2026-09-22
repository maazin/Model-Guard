"""Documented hypothesis tests used in validation and monitoring."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats


def two_sample_ks(a: np.ndarray, b: np.ndarray, feature: str, alpha: float = 0.05) -> dict[str, Any]:
    """Two-sample Kolmogorov-Smirnov test: H0 = both samples come from the same distribution.

    Assumptions: independent samples, continuous variable. Effect size = KS D statistic (max
    CDF gap). Limitation: with large n even trivial shifts are "significant", so the D statistic
    and PSI are the practical decision inputs, not the p-value alone.
    """
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    x, y = x[~np.isnan(x)], y[~np.isnan(y)]
    res = stats.ks_2samp(x, y, method="auto")
    pooled_sd = float(np.sqrt((x.var(ddof=1) + y.var(ddof=1)) / 2)) if len(x) > 1 and len(y) > 1 else float("nan")
    cohens_d = float((y.mean() - x.mean()) / pooled_sd) if pooled_sd and pooled_sd > 0 else float("nan")
    return {
        "test": "two_sample_ks",
        "feature": feature,
        "null_hypothesis": "training and comparison cohorts share the same distribution",
        "assumptions": ["independent samples", "continuous variable", "no ties correction needed"],
        "n_a": int(len(x)),
        "n_b": int(len(y)),
        "statistic": float(res.statistic),
        "p_value": float(res.pvalue),
        "alpha": alpha,
        "reject_null": bool(res.pvalue < alpha),
        "effect_size": {"ks_d": float(res.statistic), "cohens_d": cohens_d},
        "limitation": (
            "Large samples make small shifts statistically significant; interpret alongside the "
            "effect size and PSI, and note the test ignores time ordering within cohorts."
        ),
    }

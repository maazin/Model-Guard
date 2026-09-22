"""Fairness diagnostics across an explicitly approved (or synthetic) grouping field.

These are *diagnostics only*. They are never interpreted as legal compliance and the
grouping field is never used as a model feature.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from modelguard_ml.metrics import calibration


def group_metrics(
    y_true: np.ndarray, y_prob: np.ndarray, groups: pd.Series | np.ndarray, threshold: float
) -> dict[str, Any]:
    """Per-group selection rate, TPR, FPR, observed vs predicted rate; plus pairwise gaps.

    - selection_rate_ratio: min(group selection rate) / max(group selection rate).
      A common "four-fifths" rule of thumb is 0.8, treated here as a configurable diagnostic.
    - tpr_difference / fpr_difference: max - min across groups (equal-opportunity style gaps).
    - group_calibration: per-group ECE and mean predicted vs observed default rate.
    """
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_prob, dtype=float)
    g = pd.Series(np.asarray(groups)).astype(str).reset_index(drop=True)
    pred = (p >= threshold).astype(int)
    per_group: dict[str, dict[str, float | int]] = {}
    for name in sorted(g.unique()):
        m = (g == name).to_numpy()
        n = int(m.sum())
        pos = y[m] == 1
        neg = y[m] == 0
        tpr = float(pred[m][pos].mean()) if pos.any() else float("nan")
        fpr = float(pred[m][neg].mean()) if neg.any() else float("nan")
        try:
            ece = calibration(y[m], p[m], n_bins=5).ece if n >= 10 else float("nan")
        except ValueError:
            ece = float("nan")
        per_group[name] = {
            "n": n,
            "selection_rate": float(pred[m].mean()),
            "tpr": tpr,
            "fpr": fpr,
            "observed_default_rate": float(y[m].mean()),
            "mean_predicted": float(p[m].mean()),
            "ece": ece,
        }
    sel = [v["selection_rate"] for v in per_group.values()]
    tprs = [v["tpr"] for v in per_group.values() if not np.isnan(v["tpr"])]
    fprs = [v["fpr"] for v in per_group.values() if not np.isnan(v["fpr"])]
    ratio = (min(sel) / max(sel)) if sel and max(sel) > 0 else float("nan")
    return {
        "threshold": float(threshold),
        "groups": per_group,
        "selection_rate_ratio": float(ratio),
        "tpr_difference": float(max(tprs) - min(tprs)) if len(tprs) > 1 else 0.0,
        "fpr_difference": float(max(fprs) - min(fprs)) if len(fprs) > 1 else 0.0,
        "disclaimer": (
            "Diagnostic only. Computed on an explicitly approved grouping field that is never a model feature; "
            "not a legal or regulatory fairness determination."
        ),
    }

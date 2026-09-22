"""Population Stability Index and prediction-score drift."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from modelguard_shared.constants import PSI_ALERT, PSI_INVESTIGATE


def psi_from_distributions(expected: np.ndarray, actual: np.ndarray, eps: float = 1e-4) -> float:
    """PSI = sum((actual% - expected%) * ln(actual% / expected%)) with epsilon smoothing."""
    e = np.asarray(expected, dtype=float)
    a = np.asarray(actual, dtype=float)
    if e.shape != a.shape:
        raise ValueError("expected and actual bins must align")
    e = np.clip(e / e.sum() if e.sum() else e, eps, None)
    a = np.clip(a / a.sum() if a.sum() else a, eps, None)
    e = e / e.sum()
    a = a / a.sum()
    return float(np.sum((a - e) * np.log(a / e)))


def numeric_bins(baseline: np.ndarray, n_bins: int = 10) -> np.ndarray:
    """Quantile bin edges from the training baseline; stored with the monitoring plan."""
    x = np.asarray(baseline, dtype=float)
    x = x[~np.isnan(x)]
    qs = np.quantile(x, np.linspace(0, 1, n_bins + 1))
    edges = np.unique(qs)
    edges[0], edges[-1] = -np.inf, np.inf
    return edges


def numeric_psi(baseline: np.ndarray, current: np.ndarray, edges: np.ndarray | None = None) -> dict[str, Any]:
    b = np.asarray(baseline, dtype=float)
    c = np.asarray(current, dtype=float)
    b, c = b[~np.isnan(b)], c[~np.isnan(c)]
    edges = numeric_bins(b) if edges is None else np.asarray(edges, dtype=float)
    eb, _ = np.histogram(b, bins=edges)
    ab, _ = np.histogram(c, bins=edges)
    value = psi_from_distributions(eb, ab)
    return {
        "psi": value,
        "status": psi_status(value),
        "bins": [float(x) for x in edges],
        "expected_pct": (eb / max(eb.sum(), 1)).round(6).tolist(),
        "actual_pct": (ab / max(ab.sum(), 1)).round(6).tolist(),
    }


def categorical_psi(baseline: pd.Series, current: pd.Series) -> dict[str, Any]:
    levels = sorted(set(baseline.astype(str)) | set(current.astype(str)))
    e = np.array([(baseline.astype(str) == lv).sum() for lv in levels], dtype=float)
    a = np.array([(current.astype(str) == lv).sum() for lv in levels], dtype=float)
    value = psi_from_distributions(e, a)
    return {
        "psi": value,
        "status": psi_status(value),
        "bins": levels,
        "expected_pct": (e / max(e.sum(), 1)).round(6).tolist(),
        "actual_pct": (a / max(a.sum(), 1)).round(6).tolist(),
    }


def psi_status(value: float, investigate: float = PSI_INVESTIGATE, alert: float = PSI_ALERT) -> str:
    if value > alert:
        return "alert"
    if value >= investigate:
        return "investigate"
    return "stable"


def score_drift(baseline_scores: np.ndarray, current_scores: np.ndarray) -> dict[str, Any]:
    """PSI on predicted probabilities plus simple summary shifts."""
    edges = np.linspace(0, 1, 11)
    edges[0], edges[-1] = -np.inf, np.inf
    out = numeric_psi(baseline_scores, current_scores, edges)
    out.update(
        {
            "baseline_mean": float(np.mean(baseline_scores)),
            "current_mean": float(np.mean(current_scores)),
            "mean_shift": float(np.mean(current_scores) - np.mean(baseline_scores)),
        }
    )
    return out

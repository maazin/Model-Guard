"""JSON helpers that make numpy/pandas-laden payloads safe for JSON columns (incl. Postgres)."""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from typing import Any


def sanitize(obj: Any) -> Any:
    """Recursively convert numpy scalars, NaN/inf, dates and sets into plain JSON values."""
    try:
        import numpy as np
    except ImportError:  # pragma: no cover
        np = None  # type: ignore[assignment]
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple | set | frozenset):
        return [sanitize(v) for v in obj]
    if np is not None and isinstance(obj, np.ndarray):
        return [sanitize(v) for v in obj.tolist()]
    if np is not None and isinstance(obj, np.generic):
        return sanitize(obj.item())
    if isinstance(obj, bool | str | int) or obj is None:
        return obj
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    return str(obj)


def dumps(obj: Any) -> str:
    return json.dumps(sanitize(obj), allow_nan=False)

"""Derive three dated monitoring batches from the single UCI 350 snapshot (PRD 6.5).

The public dataset is one September-2005 cross-section, so monitoring batches are *generated*:
random samples of the raw sheet with deterministic, documented perturbations applied to the raw
columns. They are written in the original UCI column layout so the same adapter, checksum and
quality checks apply. Labels are carried over unchanged, so performance on shifted batches
reflects the covariate shift only. Output is git-ignored (data/sources/).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "sources" / "uci-credit-default-2005"
RAW = SRC / "default of credit card clients.xls"
OUT = SRC / "monitoring"

PAY = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
BILL = [f"BILL_AMT{i}" for i in range(1, 7)]
PAID = [f"PAY_AMT{i}" for i in range(1, 7)]

SPECS = [
    ("2005-12-31", "stable sample", {}),
    ("2006-03-31", "mild stress: bills +10%, payments -15%", {"bill_mult": 1.10, "paid_mult": 0.85}),
    (
        "2006-06-30",
        "strong stress: limits -20%, payments -40%, +1 month delinquency for 40% of rows",
        {"limit_mult": 0.80, "paid_mult": 0.60, "delinq_share": 0.40},
    ),
]


def main(n: int = 4000, seed: int = 2005) -> None:
    if not RAW.exists():
        print(f"raw file not found: {RAW}; download it first (see docs/data-sources/uci-credit-default-2005.md)")
        sys.exit(1)
    raw = pd.read_excel(RAW, header=1)
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (as_of, label, s) in enumerate(SPECS):
        rng = np.random.default_rng(seed + i)
        b = raw.sample(n=n, random_state=seed + i).reset_index(drop=True)
        b["ID"] = b["ID"] + 100_000 * (i + 1)  # distinct pseudonymous ids per batch
        if "limit_mult" in s:
            b["LIMIT_BAL"] = (b["LIMIT_BAL"] * s["limit_mult"]).round()
        if "bill_mult" in s:
            b[BILL] = (b[BILL] * s["bill_mult"]).round()
        if "paid_mult" in s:
            b[PAID] = (b[PAID] * s["paid_mult"]).round()
        if "delinq_share" in s:
            hit = rng.uniform(size=n) < s["delinq_share"]
            b.loc[hit, PAY] = (b.loc[hit, PAY].clip(lower=0) + 1).clip(upper=8)
        path = OUT / f"batch_{as_of}.csv"
        b.to_csv(path, index=False)
        print(f"wrote {path.name}: {label} (rows={n}, default_rate={b['default payment next month'].mean():.3f})")


if __name__ == "__main__":
    main()

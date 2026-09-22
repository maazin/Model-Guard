"""Synthetic loan fixture generator.

Produces data with the normalised ModelGuard schema so every test and the local demo run fully
offline. Values are drawn from simple parametric distributions with a logistic default process;
nothing here is derived from real borrowers. `shift` parameters let us manufacture drifted
monitoring batches deterministically.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from modelguard_shared.constants import EMPLOYMENT_LENGTH_LEVELS


@dataclass
class Shift:
    """Multiplicative / additive perturbations applied to a generated batch."""

    income_mult: float = 1.0
    dti_add: float = 0.0
    rate_add: float = 0.0
    loan_mult: float = 1.0
    employment_probs: list[float] | None = None
    default_logit_add: float = 0.0
    history_add: float = 0.0
    null_rate: float = 0.0
    extra: dict[str, float] = field(default_factory=dict)


def _pseudonymous_id(prefix: str, i: int) -> str:
    return "ln_" + hashlib.sha256(f"{prefix}-{i}".encode()).hexdigest()[:12]


def generate_loans(
    n: int = 6000,
    seed: int = 20240101,
    start: str = "2022-01-31",
    months: int = 24,
    shift: Shift | None = None,
    id_prefix: str = "fixture",
    include_labels: bool = True,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    s = shift or Shift()
    dates = pd.date_range(start=start, periods=months, freq="ME")
    as_of = rng.choice(dates, size=n)

    emp_probs = s.employment_probs or [0.12, 0.28, 0.22, 0.20, 0.18]
    employment = rng.choice(EMPLOYMENT_LENGTH_LEVELS, size=n, p=emp_probs)
    emp_idx = np.array([EMPLOYMENT_LENGTH_LEVELS.index(e) for e in employment])

    income = np.exp(rng.normal(np.log(62_000), 0.45, n)) * s.income_mult
    income = np.clip(income, 8_000, 900_000)
    history = np.clip(rng.gamma(6.0, 1.8, n) + emp_idx * 1.2 + s.history_add, 0.5, 45)
    dti = np.clip(rng.normal(21, 8, n) - 0.00003 * (income - 62_000) + s.dti_add, 0.5, 70)
    loan = np.clip(rng.lognormal(np.log(14_000), 0.6, n) * s.loan_mult, 500, 120_000)
    term = rng.choice([36, 60], size=n, p=[0.72, 0.28])
    rate = np.clip(
        7.0 + 0.30 * dti + 0.9 * (term == 60) - 0.12 * history + rng.normal(0, 2.0, n) + s.rate_add,
        3.5,
        34.0,
    )
    region = rng.choice(["north", "south", "east", "west"], size=n)
    fairness_group = rng.choice(["A", "B"], size=n, p=[0.6, 0.4])

    logit = (
        -2.25
        + 0.055 * (dti - 21)
        + 0.12 * (rate - 12)
        - 0.045 * (history - 10)
        - 0.35 * (np.log(income) - np.log(62_000))
        + 0.30 * (term == 60)
        + 0.15 * (loan / 14_000 - 1)
        - 0.12 * emp_idx
        + 0.10 * (fairness_group == "B")  # small synthetic base-rate gap for the fairness demo
        + 0.75 * (dti > 35)  # non-linear stress effect so a tree model has something to learn
        + 0.35 * ((term == 60) & (loan > 20_000))
        + s.default_logit_add
    )
    p_default = 1 / (1 + np.exp(-logit))
    default_flag = (rng.uniform(size=n) < p_default).astype(int)

    df = pd.DataFrame(
        {
            "loan_id": [_pseudonymous_id(id_prefix, i) for i in range(n)],
            "as_of_date": pd.to_datetime(as_of).strftime("%Y-%m-%d"),
            "default_flag": default_flag,
            "annual_income": income.round(2),
            "debt_to_income": dti.round(2),
            "loan_amount": loan.round(2),
            "interest_rate": rate.round(3),
            "term_months": term.astype(int),
            "employment_length": employment,
            "credit_history_length": history.round(2),
            "region": region,
            "fairness_group": fairness_group,
        }
    )
    if s.null_rate > 0:
        for col in ("annual_income", "debt_to_income"):
            mask = rng.uniform(size=n) < s.null_rate
            df.loc[mask, col] = np.nan
    if not include_labels:
        df = df.drop(columns=["default_flag"])
    return df


MONITORING_BATCH_SPECS: list[tuple[str, Shift]] = [
    ("2024-03-31", Shift()),
    ("2024-06-30", Shift(income_mult=0.93, dti_add=2.5, rate_add=0.8)),
    (
        "2024-09-30",
        Shift(
            income_mult=0.85,
            dti_add=9.0,
            rate_add=3.5,
            employment_probs=[0.35, 0.30, 0.15, 0.12, 0.08],
            default_logit_add=0.4,
        ),
    ),
]


def generate_monitoring_batches(n: int = 1500, seed: int = 777) -> list[tuple[str, pd.DataFrame]]:
    """Three quarterly batches: stable, mildly shifted, strongly shifted (should trip PSI alerts)."""
    out = []
    for i, (as_of, shift) in enumerate(MONITORING_BATCH_SPECS):
        df = generate_loans(n=n, seed=seed + i, start=as_of, months=1, shift=shift, id_prefix=f"batch{i}")
        df["as_of_date"] = as_of
        out.append((as_of, df))
    return out

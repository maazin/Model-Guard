"""Project-wide constants. These are configurable project defaults, not regulatory thresholds."""

from __future__ import annotations

# Normalised schema every dataset adapter must produce. `fairness_group` and `region` are
# optional and are excluded from the production-style feature set by default.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "loan_id",
    "as_of_date",
    "default_flag",
    "annual_income",
    "debt_to_income",
    "loan_amount",
    "interest_rate",
    "term_months",
    "employment_length",
    "credit_history_length",
)
OPTIONAL_COLUMNS: tuple[str, ...] = ("region", "fairness_group")

NUMERIC_FEATURES: tuple[str, ...] = (
    "annual_income",
    "debt_to_income",
    "loan_amount",
    "interest_rate",
    "term_months",
    "credit_history_length",
)
CATEGORICAL_FEATURES: tuple[str, ...] = ("employment_length",)
MODEL_FEATURES: tuple[str, ...] = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Explicitly excluded from training; rationale recorded in the model card and ADR-0004.
EXCLUDED_FEATURES: dict[str, str] = {
    "loan_id": "Identifier; no predictive meaning and would leak record identity.",
    "as_of_date": "Used only for temporal splitting and batch assignment.",
    "region": "Geographic proxy for protected characteristics; retained for monitoring only.",
    "fairness_group": "Synthetic fairness cohort used solely for diagnostics, never as a feature.",
}

# Allowed ranges used by data-quality checks (configurable project defaults).
ALLOWED_RANGES: dict[str, tuple[float, float]] = {
    "annual_income": (0.0, 5_000_000.0),
    "debt_to_income": (0.0, 100.0),
    "loan_amount": (100.0, 1_000_000.0),
    "interest_rate": (0.0, 60.0),
    "term_months": (6.0, 480.0),
    "credit_history_length": (0.0, 80.0),
}
EMPLOYMENT_LENGTH_LEVELS: tuple[str, ...] = ("<1y", "1-3y", "3-5y", "5-10y", "10y+")

# PSI guidance: configurable project defaults, not a regulatory or policy threshold.
PSI_INVESTIGATE = 0.10
PSI_ALERT = 0.25

DEMO_USERS: dict[str, str] = {
    "data_scientist": "data_scientist",
    "reviewer": "reviewer",
    "risk_leader": "risk_leader",
}

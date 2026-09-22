"""Per-source feature specification.

Every data source declares which normalised columns are model features, their allowed ranges,
categorical levels, what is deliberately excluded (and why), which field may be used for
fairness diagnostics, and whether `as_of_date` is a valid time axis. The training pipeline,
quality checks, monitoring and document rendering all read the spec instead of hard-coded
column lists, so a new dataset never has to pretend to have someone else's schema.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from modelguard_shared.constants import (
    ALLOWED_RANGES,
    EMPLOYMENT_LENGTH_LEVELS,
    EXCLUDED_FEATURES,
    NUMERIC_FEATURES,
)

CORE_COLUMNS: tuple[str, ...] = ("loan_id", "as_of_date", "default_flag")


@dataclass(frozen=True)
class DictionaryRow:
    source_field: str
    normalized_field: str
    type: str
    allowed_range: str
    transformation: str
    feature_use: str


@dataclass(frozen=True)
class FeatureSpec:
    source_id: str
    numeric: tuple[str, ...]
    categorical: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    excluded: dict[str, str] = field(default_factory=dict)
    fairness_field: str | None = None
    monitoring_only: tuple[str, ...] = ()
    time_field_valid: bool = True
    target_definition: str = ""
    dictionary: tuple[DictionaryRow, ...] = ()

    @property
    def features(self) -> tuple[str, ...]:
        return self.numeric + tuple(self.categorical)

    @property
    def required_columns(self) -> tuple[str, ...]:
        return CORE_COLUMNS + self.features

    @property
    def optional_columns(self) -> tuple[str, ...]:
        extra = tuple(c for c in (self.fairness_field,) if c) + self.monitoring_only
        return tuple(dict.fromkeys(extra))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["categorical"] = {k: list(v) for k, v in self.categorical.items()}
        d["ranges"] = {k: list(v) for k, v in self.ranges.items()}
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FeatureSpec:
        return cls(
            source_id=d["source_id"],
            numeric=tuple(d["numeric"]),
            categorical={k: tuple(v) for k, v in d.get("categorical", {}).items()},
            ranges={k: (float(v[0]), float(v[1])) for k, v in d.get("ranges", {}).items()},
            excluded=dict(d.get("excluded", {})),
            fairness_field=d.get("fairness_field"),
            monitoring_only=tuple(d.get("monitoring_only", ())),
            time_field_valid=bool(d.get("time_field_valid", True)),
            target_definition=d.get("target_definition", ""),
            dictionary=tuple(DictionaryRow(**r) for r in d.get("dictionary", ())),
        )

    def dictionary_markdown(self) -> str:
        head = "| Source field | Normalised field | Type | Allowed range | Transformation | Feature use |\n| --- | --- | --- | --- | --- | --- |\n"
        return head + "\n".join(
            f"| {r.source_field} | {r.normalized_field} | {r.type} | {r.allowed_range} | {r.transformation} | {r.feature_use} |"
            for r in self.dictionary
        )


def _rng(col: str) -> str:
    lo, hi = ALLOWED_RANGES[col]
    return f"{lo:,.0f} – {hi:,.0f}"


SYNTHETIC_SPEC = FeatureSpec(
    source_id="synthetic-loans-v1",
    numeric=NUMERIC_FEATURES,
    categorical={"employment_length": EMPLOYMENT_LENGTH_LEVELS},
    ranges=dict(ALLOWED_RANGES),
    excluded=dict(EXCLUDED_FEATURES),
    fairness_field="fairness_group",
    monitoring_only=("region",),
    time_field_valid=True,
    target_definition="`default_flag` = 1 when the synthetic borrower defaults within the observation window.",
    dictionary=(
        DictionaryRow("loan_id", "loan_id", "string", "pseudonymous hash", "none", "excluded (identifier)"),
        DictionaryRow("as_of_date", "as_of_date", "date", "2022-01 .. 2023-12", "parsed to date", "split/batch only"),
        DictionaryRow("default_flag", "default_flag", "boolean", "{0,1}", "none", "target"),
        DictionaryRow(
            "annual_income",
            "annual_income",
            "numeric",
            _rng("annual_income"),
            "median impute, standard scale",
            "feature",
        ),
        DictionaryRow(
            "debt_to_income",
            "debt_to_income",
            "numeric",
            _rng("debt_to_income"),
            "median impute, standard scale",
            "feature",
        ),
        DictionaryRow(
            "loan_amount", "loan_amount", "numeric", _rng("loan_amount"), "median impute, standard scale", "feature"
        ),
        DictionaryRow(
            "interest_rate",
            "interest_rate",
            "numeric",
            _rng("interest_rate"),
            "median impute, standard scale",
            "feature",
        ),
        DictionaryRow(
            "term_months", "term_months", "integer", _rng("term_months"), "median impute, standard scale", "feature"
        ),
        DictionaryRow("employment_length", "employment_length", "categorical", "5 fixed levels", "one-hot", "feature"),
        DictionaryRow(
            "credit_history_length",
            "credit_history_length",
            "numeric",
            _rng("credit_history_length"),
            "median impute, standard scale",
            "feature",
        ),
        DictionaryRow("region", "region", "categorical", "4 levels", "none", "excluded; monitoring only"),
        DictionaryRow(
            "fairness_group",
            "fairness_group",
            "categorical",
            "synthetic A/B",
            "none",
            "excluded; fairness diagnostics only",
        ),
    ),
)

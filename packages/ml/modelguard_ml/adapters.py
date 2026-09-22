"""Pluggable dataset adapters (ADR-0001).

An adapter turns a source file into the normalised ModelGuard schema. The synthetic fixture is
already normalised; a real public dataset gets a `ColumnMapAdapter` with an explicit mapping and
per-field transformations documented in `docs/data-sources/<source_id>.md`. Adapters never
download anything: the file must already be under `data/`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import pandas as pd
from modelguard_shared.constants import OPTIONAL_COLUMNS, REQUIRED_COLUMNS


class DatasetAdapter(Protocol):
    source_id: str

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame: ...


@dataclass
class PassthroughAdapter:
    """For files already in the normalised schema (the synthetic fixture)."""

    source_id: str = "synthetic-loans-v1"

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        keep = [c for c in REQUIRED_COLUMNS + OPTIONAL_COLUMNS if c in raw.columns]
        return raw[keep].copy()


@dataclass
class ColumnMapAdapter:
    """Rename source columns and apply documented transformations.

    `mapping` maps normalised field -> source column; `transforms` maps normalised field -> callable
    applied after renaming (e.g. percent to ratio, months to years).
    """

    source_id: str
    mapping: dict[str, str]
    transforms: dict[str, Callable[[pd.Series], pd.Series]] = field(default_factory=dict)

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        missing = [src for src in self.mapping.values() if src not in raw.columns]
        if missing:
            raise ValueError(f"source columns missing for adapter {self.source_id}: {missing}")
        out = pd.DataFrame({norm: raw[src] for norm, src in self.mapping.items()})
        for col, fn in self.transforms.items():
            out[col] = fn(out[col])
        return out


ADAPTERS: dict[str, DatasetAdapter] = {"synthetic-loans-v1": PassthroughAdapter()}


def get_adapter(source_id: str) -> DatasetAdapter:
    return ADAPTERS.get(source_id, PassthroughAdapter(source_id))

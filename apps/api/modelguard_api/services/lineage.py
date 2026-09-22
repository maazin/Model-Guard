from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from modelguard_ml.adapters import get_adapter
from modelguard_ml.data_quality import profile, run_quality_checks
from modelguard_shared.hashing import sha256_file, sha256_text
from modelguard_shared.jsonutil import sanitize
from sqlalchemy.orm import Session

from modelguard_api.config import ROOT, get_settings
from modelguard_api.errors import bad_request, not_found
from modelguard_api.models import DataSnapshot, DataSource, User
from modelguard_api.services.audit import record_event

SOURCE_DOC_TEMPLATE = """---
source_id: {id}
name: {name}
license_url: {license_url}
license_name: {license_name}
retrieval_date: {retrieval_date}
license_confirmed_by: {confirmed_by}
---

# Data source: {name}

- **Source URL / reference:** {license_url}
- **License:** {license_name}
- **Allowed use:** {intended_use}
- **Retrieval date:** {retrieval_date}
- **Checksum of raw file:** recorded per snapshot in the registry

## Intended use in ModelGuard

{intended_use}

## Schema

Normalised to the ModelGuard schema (see `docs/governance/templates/data_lineage.md` data dictionary).

## Limitations

{limitations}
"""


def register_source(db: Session, payload: dict, user: User) -> DataSource:
    if db.get(DataSource, payload["id"]):
        raise bad_request(f"data source '{payload['id']}' already exists")
    doc_dir = get_settings().docs_dir / "data-sources"
    doc_dir.mkdir(parents=True, exist_ok=True)
    doc_path = doc_dir / f"{payload['id']}.md"
    if not doc_path.exists():
        doc_path.write_text(SOURCE_DOC_TEMPLATE.format(confirmed_by=user.username, **payload))
    src = DataSource(
        **payload,
        doc_path=str(doc_path.relative_to(ROOT)) if doc_path.is_relative_to(ROOT) else str(doc_path),
        license_confirmed_by=user.username,
    )
    db.add(src)
    record_event(
        db,
        actor_id=user.username,
        action="data_source.registered",
        entity_type="data_source",
        entity_id=src.id,
        after=payload,
    )
    db.commit()
    return src


def _resolve_import_path(file_path: str) -> Path:
    """Only files under data/ (fixtures or licensed sources) may be imported."""
    p = Path(file_path)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    allowed = (ROOT / "data").resolve()
    if not p.is_relative_to(allowed):
        raise bad_request("file_path must be inside the repository data/ directory")
    if not p.exists():
        raise bad_request(f"file not found: {file_path}")
    return p


def load_frame(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def import_snapshot(
    db: Session, *, source_id: str, file_path: str, as_of_date: str, purpose: str, user: User
) -> DataSnapshot:
    if not db.get(DataSource, source_id):
        raise not_found("data source", source_id)
    path = _resolve_import_path(file_path)
    df = get_adapter(source_id).normalize(load_frame(path))
    report = run_quality_checks(df, require_target=(purpose == "training"))
    snap = DataSnapshot(
        source_id=source_id,
        file_path=str(path.relative_to(ROOT)),
        as_of_date=as_of_date,
        row_count=len(df),
        checksum=sha256_file(path),
        schema_hash=sha256_text(json.dumps({c: str(t) for c, t in df.dtypes.items()}, sort_keys=True)),
        quality_status=report.status,
        quality_json=sanitize(report.to_dict()),
        profile_json=sanitize(profile(df)),
        purpose=purpose,
    )
    db.add(snap)
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action="snapshot.imported",
        entity_type="data_snapshot",
        entity_id=snap.id,
        after={"source_id": source_id, "checksum": snap.checksum, "rows": snap.row_count, "quality": report.status},
    )
    db.commit()
    return snap

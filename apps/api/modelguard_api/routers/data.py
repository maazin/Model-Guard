from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api import schemas
from modelguard_api.auth import current_user, require_role
from modelguard_api.db import get_db
from modelguard_api.errors import not_found
from modelguard_api.models import DataSnapshot, DataSource, User
from modelguard_api.services import lineage

router = APIRouter(prefix="/api/v1", tags=["data"])


@router.post("/data-sources", response_model=schemas.DataSourceOut, status_code=201)
def create_source(
    payload: schemas.DataSourceIn, db: Session = Depends(get_db), user: User = Depends(require_role("data_scientist"))
):
    return lineage.register_source(db, payload.model_dump(), user)


@router.get("/data-sources", response_model=list[schemas.DataSourceOut])
def list_sources(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return list(db.scalars(select(DataSource).order_by(DataSource.created_at)))


@router.get("/data-sources/{source_id}", response_model=schemas.DataSourceOut)
def get_source(source_id: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    src = db.get(DataSource, source_id)
    if src is None:
        raise not_found("data source", source_id)
    return src


@router.post("/snapshots/import", response_model=schemas.SnapshotOut, status_code=201)
def import_snapshot(
    payload: schemas.SnapshotImportIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist")),
):
    return lineage.import_snapshot(
        db,
        source_id=payload.source_id,
        file_path=payload.file_path,
        as_of_date=payload.as_of_date,
        purpose=payload.purpose,
        user=user,
    )


@router.get("/snapshots", response_model=list[schemas.SnapshotOut])
def list_snapshots(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return list(db.scalars(select(DataSnapshot).order_by(DataSnapshot.as_of_date)))


@router.get("/snapshots/{snapshot_id}", response_model=schemas.SnapshotOut)
def get_snapshot(snapshot_id: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    snap = db.get(DataSnapshot, snapshot_id)
    if snap is None:
        raise not_found("snapshot", snapshot_id)
    return snap

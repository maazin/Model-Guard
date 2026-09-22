from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api import schemas
from modelguard_api.auth import current_user
from modelguard_api.db import get_db
from modelguard_api.models import ModelVersion, User
from modelguard_api.services import audit, executive, registry

router = APIRouter(prefix="/api/v1", tags=["governance"])


@router.get("/executive-summary/{ident}")
def executive_summary(ident: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    out = executive.summary(db, registry.get_version(db, ident))
    db.commit()
    return out


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db), _: User = Depends(current_user)):
    """Overview: every version with a compact executive summary."""
    versions = list(db.scalars(select(ModelVersion).order_by(ModelVersion.created_at)))
    out = [executive.summary(db, mv) for mv in versions]
    db.commit()
    return {"versions": out}


@router.get("/audit-events", response_model=list[schemas.AuditEventOut])
def audit_events(
    entity_id: str | None = None, limit: int = 200, db: Session = Depends(get_db), _: User = Depends(current_user)
):
    return audit.list_events(db, entity_id=entity_id, limit=limit)


@router.get("/audit-events/verify")
def verify_audit(db: Session = Depends(get_db), _: User = Depends(current_user)):
    r = audit.verify(db)
    return {"valid": r.valid, "checked": r.checked, "first_bad_index": r.first_bad_index, "detail": r.detail}


@router.get("/users", response_model=list[schemas.UserOut])
def users(db: Session = Depends(get_db)):
    return list(db.scalars(select(User).order_by(User.username)))


@router.get("/me", response_model=schemas.UserOut)
def me(user: User = Depends(current_user)):
    return user

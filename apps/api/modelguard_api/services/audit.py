from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from modelguard_governance.audit import GENESIS_HASH, ChainVerification, compute_event_hash, verify_chain
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api.models import AuditEvent


def record_event(
    db: Session,
    *,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: Any = None,
    after: Any = None,
) -> AuditEvent:
    """Append one event to the hash chain. Never updates or deletes existing rows."""
    last = db.scalar(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(1))
    prev = last.event_hash if last else GENESIS_HASH
    payload = {
        "actor_id": actor_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "before_json": before,
        "after_json": after,
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    ev = AuditEvent(**payload, previous_hash=prev, event_hash=compute_event_hash(prev, payload))
    db.add(ev)
    db.flush()
    return ev


def event_to_dict(ev: AuditEvent) -> dict[str, Any]:
    return {
        "id": ev.id,
        "actor_id": ev.actor_id,
        "action": ev.action,
        "entity_type": ev.entity_type,
        "entity_id": ev.entity_id,
        "before_json": ev.before_json,
        "after_json": ev.after_json,
        "occurred_at": ev.occurred_at,
        "previous_hash": ev.previous_hash,
        "event_hash": ev.event_hash,
    }


def list_events(db: Session, entity_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    q = select(AuditEvent).order_by(AuditEvent.id.asc())
    if entity_id:
        q = q.where(AuditEvent.entity_id == entity_id)
    return [event_to_dict(e) for e in db.scalars(q.limit(limit))]


def verify(db: Session) -> ChainVerification:
    events = [event_to_dict(e) for e in db.scalars(select(AuditEvent).order_by(AuditEvent.id.asc()))]
    return verify_chain(events)

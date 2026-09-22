"""Append-only audit events with a SHA-256 hash chain.

event_hash = sha256(previous_hash + canonical_event_payload). Any edit to a stored payload
changes its recomputed hash and breaks every later link, so tampering is visible on verify.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modelguard_shared.hashing import canonical_json, sha256_text

GENESIS_HASH = "0" * 64


def canonical_payload(event: dict[str, Any]) -> str:
    fields = ("actor_id", "action", "entity_type", "entity_id", "before_json", "after_json", "occurred_at")
    return canonical_json({k: event.get(k) for k in fields})


def compute_event_hash(previous_hash: str, event: dict[str, Any]) -> str:
    return sha256_text(previous_hash + canonical_payload(event))


@dataclass
class ChainVerification:
    valid: bool
    checked: int
    first_bad_index: int | None = None
    detail: str | None = None


def verify_chain(events: list[dict[str, Any]]) -> ChainVerification:
    """Events must be ordered oldest -> newest and carry previous_hash + event_hash."""
    prev = GENESIS_HASH
    for i, ev in enumerate(events):
        if ev.get("previous_hash") != prev:
            return ChainVerification(False, i, i, f"previous_hash mismatch at event {i}")
        expected = compute_event_hash(prev, ev)
        if ev.get("event_hash") != expected:
            return ChainVerification(False, i, i, f"event_hash mismatch at event {i}")
        prev = expected
    return ChainVerification(True, len(events))

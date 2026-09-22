"""Deterministic hashing helpers (checksums, canonical JSON, audit hash chain)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    """SHA-256 of a file's bytes, streamed so large raw files don't need to fit in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(payload: Any) -> str:
    """Stable JSON serialisation: sorted keys, no whitespace, ISO-ish default for odd types."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def sha256_canonical(payload: Any) -> str:
    return sha256_text(canonical_json(payload))

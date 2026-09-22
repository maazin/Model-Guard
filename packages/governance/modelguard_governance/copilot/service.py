"""Copilot orchestration: filter documents -> retrieve -> provider -> validated response."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

from modelguard_governance.copilot.provider import CopilotContext, LLMProvider, RuleBasedProvider
from modelguard_governance.copilot.retrieval import Chunk, LocalIndex, chunk_document
from modelguard_governance.copilot.schema import CopilotResponse, safe_fallback

MAX_QUESTION_CHARS = 1000
# Anything that looks like a borrower-level record must never reach a prompt.
RAW_ROW_PATTERN = re.compile(r"\bln_[0-9a-f]{12}\b|\bloan_id\s*[:=]", re.IGNORECASE)


@dataclass
class CopilotResult:
    response: CopilotResponse
    provider: str
    latency_ms: int
    cited_document_ids: list[str]
    status: str


def build_index(documents: list[dict[str, Any]]) -> LocalIndex:
    """documents: [{id, type, content, status}] — only approved/complete-or-draft governance docs."""
    chunks: list[Chunk] = []
    for d in documents:
        chunks.extend(chunk_document(d["id"], d["type"], d["content"]))
    return LocalIndex(chunks)


def answer_question(
    *,
    question: str,
    model_version: str,
    state: str,
    documents: list[dict[str, Any]],
    readiness: list[dict[str, Any]],
    provider: LLMProvider | None = None,
    k: int = 6,
) -> CopilotResult:
    start = time.perf_counter()
    provider = provider or RuleBasedProvider()
    q = question.strip()[:MAX_QUESTION_CHARS]
    if not q:
        return CopilotResult(safe_fallback("empty question"), provider.name, 0, [], "rejected")
    if RAW_ROW_PATTERN.search(q):
        return CopilotResult(
            safe_fallback("question appears to contain borrower-level identifiers"),
            provider.name,
            0,
            [],
            "rejected",
        )
    index = build_index(documents)
    hits = index.search(q, k=k)
    ctx = CopilotContext(question=q, model_version=model_version, readiness=readiness, chunks=hits, state=state)
    try:
        response = provider.generate(ctx)
        status = "ok"
    except Exception as exc:  # noqa: BLE001
        response = safe_fallback(f"provider error: {type(exc).__name__}")
        status = "fallback"
    latency = int((time.perf_counter() - start) * 1000)
    cited = sorted({c.document_id for c in response.citations})
    return CopilotResult(response, provider.name, latency, cited, status)

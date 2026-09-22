from __future__ import annotations

from modelguard_governance.copilot.provider import select_provider
from modelguard_governance.copilot.service import CopilotResult, answer_question
from sqlalchemy.orm import Session

from modelguard_api.config import get_settings
from modelguard_api.models import CopilotQuery, ModelVersion, User
from modelguard_api.services import documents as docsvc
from modelguard_api.services.readiness import evaluate_and_store


def query(db: Session, mv: ModelVersion, question: str, user: User, provider_name: str | None = None) -> CopilotResult:
    docs = [
        {"id": f"{d.type}-{mv.semantic_version}", "type": d.type, "content": d.content, "status": d.status}
        for d in docsvc.get_documents(db, mv)
    ]
    readiness = [r.to_dict() for r in evaluate_and_store(db, mv)]
    provider = select_provider(provider_name or get_settings().llm_provider)
    result = answer_question(
        question=question,
        model_version=mv.semantic_version,
        state=mv.state,
        documents=docs,
        readiness=readiness,
        provider=provider,
    )
    # Log metadata only: never the question text.
    db.add(
        CopilotQuery(
            model_version_id=mv.id,
            provider=result.provider,
            cited_document_ids=result.cited_document_ids,
            status=result.status,
            latency_ms=result.latency_ms,
            question_length=len(question),
        )
    )
    db.commit()
    return result

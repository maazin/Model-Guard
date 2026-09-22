from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from modelguard_governance.documents import DocumentType
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api import schemas
from modelguard_api.auth import current_user, require_role
from modelguard_api.db import get_db
from modelguard_api.errors import bad_request, not_found
from modelguard_api.models import Alert, ApprovalDecision, MetricResult, ModelVersion, User, ValidationArtifact
from modelguard_api.services import audit, copilot, executive, monitoring, readiness, registry
from modelguard_api.services import documents as docsvc

router = APIRouter(prefix="/api/v1/model-versions", tags=["model-versions"])


@router.post("", response_model=schemas.ModelVersionOut, status_code=201)
def register(
    payload: schemas.ModelVersionIn, db: Session = Depends(get_db), user: User = Depends(require_role("data_scientist"))
):
    return registry.register_version(
        db,
        training_run_id=payload.training_run_id,
        semantic_version=payload.semantic_version,
        model_type=payload.model_type,
        description=payload.description,
        user=user,
    )


@router.get("", response_model=list[schemas.ModelVersionOut])
def list_versions(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return list(db.scalars(select(ModelVersion).order_by(ModelVersion.created_at)))


@router.get("/{ident}", response_model=schemas.ModelVersionDetailOut)
def detail(ident: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    mv = registry.get_version(db, ident)
    run = mv.training_run
    checks = readiness.stored_results(db, mv) or [r.to_dict() for r in readiness.evaluate_and_store(db, mv)]
    db.commit()
    return {
        **{c: getattr(mv, c) for c in schemas.ModelVersionOut.model_fields},
        "training_run": run,
        "snapshot": run.snapshot,
        "source": run.snapshot.source,
        "metrics": list(db.scalars(select(MetricResult).where(MetricResult.model_version_id == mv.id))),
        "artifacts": {
            a.name: a.payload_json
            for a in db.scalars(select(ValidationArtifact).where(ValidationArtifact.model_version_id == mv.id))
        },
        "documents": docsvc.get_documents(db, mv),
        "controls": registry.get_controls(db, mv),
        "readiness": checks,
        "decisions": list(
            db.scalars(
                select(ApprovalDecision)
                .where(ApprovalDecision.model_version_id == mv.id)
                .order_by(ApprovalDecision.decided_at)
            )
        ),
        "alerts": monitoring.alerts_for(db, mv),
        "audit_events": audit.list_events(db, entity_id=mv.id),
        "narrative": mv.narrative_json or {},
    }


@router.post("/{ident}/validate", response_model=schemas.ModelVersionOut)
def validate(ident: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return registry.validate_version(db, registry.get_version(db, ident), user)


@router.get("/{ident}/readiness", response_model=list[schemas.ReadinessOut])
def readiness_checks(ident: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    mv = registry.get_version(db, ident)
    results = [r.to_dict() for r in readiness.evaluate_and_store(db, mv)]
    db.commit()
    return results


@router.post("/{ident}/submit-review", response_model=schemas.ModelVersionOut)
def submit_review(ident: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return registry.submit_review(db, registry.get_version(db, ident), user)


@router.post("/{ident}/decision", response_model=schemas.ModelVersionOut)
def decision(
    ident: str, payload: schemas.DecisionIn, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    return registry.decide(db, registry.get_version(db, ident), payload.decision, payload.rationale, user)


@router.post("/{ident}/retire", response_model=schemas.ModelVersionOut)
def retire(ident: str, payload: schemas.RetireIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return registry.retire(db, registry.get_version(db, ident), payload.reason, user)


@router.post("/{ident}/reopen", response_model=schemas.ModelVersionOut)
def reopen(ident: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return registry.reopen(db, registry.get_version(db, ident), user)


@router.put("/{ident}/narrative", response_model=list[schemas.DocumentOut])
def narrative(
    ident: str,
    payload: schemas.NarrativeIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist")),
):
    return registry.set_narrative(db, registry.get_version(db, ident), payload.narrative, user)


@router.put("/{ident}/controls", response_model=list[schemas.ControlOut])
def controls(
    ident: str,
    payload: list[schemas.ControlIn],
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist")),
):
    return registry.replace_controls(db, registry.get_version(db, ident), [c.model_dump() for c in payload], user)


@router.get("/{ident}/documents/{doc_type}", response_model=schemas.DocumentDetailOut)
def document(ident: str, doc_type: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    mv = registry.get_version(db, ident)
    doc = next((d for d in docsvc.get_documents(db, mv) if d.type == doc_type), None)
    if doc is None:
        raise not_found("document", doc_type)
    return doc


@router.get("/{ident}/documents/{doc_type}/download", response_class=PlainTextResponse)
def download_document(ident: str, doc_type: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    mv = registry.get_version(db, ident)
    doc = next((d for d in docsvc.get_documents(db, mv) if d.type == doc_type), None)
    if doc is None:
        raise not_found("document", doc_type)
    return PlainTextResponse(
        doc.content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{mv.semantic_version}-{doc_type}.md"'},
    )


@router.put("/{ident}/documents/{doc_type}/status", response_model=schemas.DocumentOut)
def document_status(
    ident: str,
    doc_type: str,
    payload: schemas.DocumentStatusIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist")),
):
    try:
        dt = DocumentType(doc_type)
    except ValueError as exc:
        raise bad_request(f"unknown document type {doc_type}") from exc
    return registry.set_document_status(db, registry.get_version(db, ident), dt, payload.status, user)


@router.post("/{ident}/monitoring-batches", response_model=schemas.MonitoringBatchOut, status_code=201)
def run_monitoring(
    ident: str,
    payload: schemas.MonitoringBatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist", "reviewer")),
):
    return monitoring.run_batch(db, registry.get_version(db, ident), snapshot_id=payload.snapshot_id, user=user)


@router.get("/{ident}/monitoring")
def get_monitoring(ident: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    mv = registry.get_version(db, ident)
    batches = monitoring.batches_for(db, mv)
    alerts = monitoring.alerts_for(db, mv)
    return {
        "model_version": mv.semantic_version,
        "state": mv.state,
        "thresholds": monitoring.thresholds_for(db, mv),
        "holdout_auc": mv.training_run.metrics_json.get(mv.model_type, {})
        .get("metrics", {})
        .get("auc", {})
        .get("value"),
        "batches": [schemas.MonitoringBatchOut.model_validate(b).model_dump() for b in batches],
        "alerts": [schemas.AlertOut.model_validate(a).model_dump() for a in alerts],
    }


@router.patch("/{ident}/alerts/{alert_id}", response_model=schemas.AlertOut)
def update_alert(
    ident: str,
    alert_id: str,
    payload: schemas.AlertUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist", "reviewer")),
):
    mv = registry.get_version(db, ident)
    alert = db.get(Alert, alert_id)
    if alert is None or alert.model_version_id != mv.id:
        raise not_found("alert", alert_id)
    return monitoring.update_alert(db, alert, status=payload.status, note=payload.note, user=user)


@router.post("/{ident}/copilot/query", response_model=schemas.CopilotQueryOut)
def copilot_query(
    ident: str, payload: schemas.CopilotQueryIn, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    result = copilot.query(db, registry.get_version(db, ident), payload.question, user, payload.provider)
    return {
        "response": result.response.model_dump(),
        "provider": result.provider,
        "latency_ms": result.latency_ms,
        "cited_document_ids": result.cited_document_ids,
        "status": result.status,
    }


@router.get("/{ident}/executive-summary")
def executive_summary_alias(ident: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    out = executive.summary(db, registry.get_version(db, ident))
    db.commit()
    return out

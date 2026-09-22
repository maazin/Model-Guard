"""Assemble evidence from the registry and persist readiness results."""

from __future__ import annotations

from pathlib import Path

from modelguard_governance.documents import DocumentType, parse_front_matter
from modelguard_governance.readiness import CheckResult, ReadinessEvidence, evaluate
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api.config import ROOT
from modelguard_api.models import MetricResult, ModelVersion, ReadinessCheck, ValidationArtifact
from modelguard_api.services import documents as docsvc
from modelguard_api.services import security


def assemble_evidence(db: Session, mv: ModelVersion) -> ReadinessEvidence:
    from modelguard_api.services.registry import get_controls, latest_decision

    run = mv.training_run
    snap = run.snapshot
    src = snap.source
    docs = {
        d.type: {"status": d.status, "content": d.content, "content_hash": d.content_hash, "path": d.path}
        for d in docsvc.get_documents(db, mv)
    }
    metrics = {
        m.metric_name
        for m in db.scalars(
            select(MetricResult).where(MetricResult.model_version_id == mv.id, MetricResult.scope == "holdout")
        )
    }
    artifacts = {
        a.name for a in db.scalars(select(ValidationArtifact).where(ValidationArtifact.model_version_id == mv.id))
    }
    plan_meta = (
        parse_front_matter(docs[DocumentType.MONITORING_PLAN.value]["content"])[0]
        if DocumentType.MONITORING_PLAN.value in docs
        else {}
    )
    risk_meta = (
        parse_front_matter(docs[DocumentType.RISK_ASSESSMENT.value]["content"])[0]
        if DocumentType.RISK_ASSESSMENT.value in docs
        else {}
    )
    reason = risk_meta.get("fairness_unavailable_reason")
    reason = None if reason in (None, "null", "", "TODO") else str(reason)
    decision = latest_decision(db, mv)
    scan = security.scan_for_secrets(
        [ROOT / "apps" / "api", ROOT / "packages", ROOT / "docs", Path(run.artifact_dir or ROOT / "artifacts")]
    )
    leak = security.raw_rows_present([d["content"] for d in docs.values()] + [str(run.config_json)])
    return ReadinessEvidence(
        source={
            "id": src.id,
            "doc_path": src.doc_path if (ROOT / src.doc_path).exists() else None,
            "retrieval_date": src.retrieval_date,
            "license_url": src.license_url,
        },
        snapshot={"checksum": snap.checksum, "quality_status": snap.quality_status},
        documents=docs,
        holdout_metrics=metrics,
        validation_artifacts=artifacts,
        monitoring_plan={
            "psi_bins": plan_meta.get("psi_bins"),
            "alert_thresholds": plan_meta.get("alert_thresholds") or {},
            "owner": plan_meta.get("owner") if plan_meta.get("owner") not in ("TODO", None) else None,
        },
        has_baseline_distributions="baseline_distributions" in artifacts,
        fairness_metrics_present="fairness" in artifacts,
        fairness_unavailable_reason=reason,
        controls=[
            {
                "control_name": c.control_name,
                "owner": c.owner,
                "frequency": c.frequency,
                "status": c.status,
                "evidence_uri": c.evidence_uri,
            }
            for c in get_controls(db, mv)
        ],
        security={
            "secrets_scan": scan["status"],
            "files_scanned": scan["files_scanned"],
            "raw_rows_in_logs": leak,
            "findings": scan["findings"],
        },
        signoff={"reviewer_id": decision.reviewer_id, "decision": decision.decision, "rationale": decision.rationale}
        if decision
        else None,
    )


def evaluate_and_store(db: Session, mv: ModelVersion) -> list[CheckResult]:
    results = evaluate(assemble_evidence(db, mv))
    db.query(ReadinessCheck).filter(ReadinessCheck.model_version_id == mv.id).delete()
    for r in results:
        db.add(
            ReadinessCheck(
                model_version_id=mv.id,
                check_name=r.check_name,
                status=r.status,
                missing_json=r.missing,
                evidence_json=r.evidence,
            )
        )
    db.flush()
    return results


def stored_results(db: Session, mv: ModelVersion) -> list[dict]:
    rows = db.scalars(select(ReadinessCheck).where(ReadinessCheck.model_version_id == mv.id)).all()
    return [
        {
            "check_name": r.check_name,
            "status": r.status,
            "missing": r.missing_json,
            "evidence": r.evidence_json,
            "evaluated_at": r.evaluated_at.isoformat(),
        }
        for r in rows
    ]

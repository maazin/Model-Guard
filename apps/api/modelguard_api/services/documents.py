"""Document rendering/persistence for a model version."""

from __future__ import annotations

import json
from typing import Any

from modelguard_governance.documents import DocumentType, dump_document, parse_front_matter, render_template
from modelguard_shared.constants import PSI_ALERT, PSI_INVESTIGATE
from modelguard_shared.hashing import sha256_text
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api.config import ROOT, get_settings
from modelguard_api.models import Control, Document, ModelVersion, User
from modelguard_api.services.audit import record_event

DEFAULT_AUC_DROP = 0.05


def base_context(db: Session, mv: ModelVersion) -> dict[str, Any]:
    run = mv.training_run
    snap = run.snapshot
    src = snap.source
    cfg = run.config_json or {}
    split = cfg.get("split", {})
    counts = split.get("counts", {})
    excluded = "\n".join(f"- `{k}`: {v}" for k, v in (cfg.get("excluded_features") or {}).items())
    algo = "HistGradientBoostingClassifier" if mv.model_type == "champion" else "LogisticRegression (L2)"
    return {
        "version": mv.semantic_version,
        "model_uuid": mv.id,
        "model_type": mv.model_type,
        "model_algorithm": algo,
        "training_run_id": run.id,
        "git_sha": run.git_sha or "n/a",
        "created_at": mv.created_at.isoformat(timespec="seconds"),
        "state": mv.state,
        "source_id": src.id,
        "source_name": src.name,
        "license_url": src.license_url,
        "retrieval_date": src.retrieval_date,
        "source_doc_path": src.doc_path,
        "intended_use_short": src.intended_use[:160],
        "snapshot_id": snap.id,
        "snapshot_as_of": snap.as_of_date,
        "snapshot_checksum": snap.checksum,
        "row_count": snap.row_count,
        "features": ", ".join(f"`{f}`" for f in cfg.get("features", [])),
        "excluded_rationale": excluded or None,
        "split_strategy": split.get("strategy"),
        "split_train": counts.get("train"),
        "split_validation": counts.get("validation"),
        "split_test": counts.get("test"),
        "seed": cfg.get("random_seed"),
        "hyperparameters": json.dumps((cfg.get("hyperparameters") or {}).get(mv.model_type, {})),
        "package_versions": json.dumps(cfg.get("package_versions", {})),
        "threshold": cfg.get("illustrative_threshold"),
        "quality_summary": _quality_summary(snap.quality_json),
        "psi_bins": (run.baseline_distributions_json or {}).get("psi_bins", 10),
        "psi_investigate": PSI_INVESTIGATE,
        "psi_alert": PSI_ALERT,
        "auc_drop": DEFAULT_AUC_DROP,
        "baseline_summary": _baseline_summary(run.baseline_distributions_json),
        "controls_table": controls_table(db, mv),
        "controls_summary": controls_table(db, mv),
        "reviewer_status": "Pending human review. Approval state is tracked in the registry.",
        "readiness_checklist": "Readiness is evaluated live by the deterministic readiness engine; see the Governance page.",
        "fairness_unavailable_reason": "null",
        "changes": f"- {mv.created_at.date()}: `{mv.semantic_version}` registered from training run `{run.id}` ({mv.model_type}).",
    }


def _quality_summary(q: dict[str, Any] | None) -> str | None:
    if not q:
        return None
    issues = q.get("issues") or []
    lines = [
        f"- Status: **{q.get('status')}**; rows {q.get('row_count')}; duplicate rate {q.get('duplicate_rate', 0):.2%}; "
        f"target rate {q.get('target_rate') if q.get('target_rate') is not None else 'n/a'}",
    ]
    lines += [f"- {i['severity']}: {i['check']} — {i['detail']}" for i in issues] or ["- No issues raised."]
    return "\n".join(lines)


def _baseline_summary(b: dict[str, Any] | None) -> str | None:
    if not b:
        return None
    nums = ", ".join(f"`{k}`" for k in b.get("numeric", {}))
    cats = ", ".join(f"`{k}`" for k in b.get("categorical", {}))
    return (
        f"Stored from the training cohort (train default rate {b.get('train_default_rate', 0):.3f}): "
        f"quantile bins for {nums}; level proportions for {cats}; score histogram mean {b.get('scores', {}).get('mean', 0):.3f}."
    )


def controls_table(db: Session, mv: ModelVersion) -> str | None:
    rows = list(db.scalars(select(Control).where(Control.model_version_id == mv.id).order_by(Control.control_name)))
    if not rows:
        return None
    head = "| Control | Owner | Frequency | Status | Test evidence | Evidence URI |\n| --- | --- | --- | --- | --- | --- |\n"
    return head + "\n".join(
        f"| {c.control_name} | {c.owner} | {c.frequency} | {c.status} | {c.test_evidence or '—'} | {c.evidence_uri or '—'} |"
        for c in rows
    )


def doc_path_for(mv: ModelVersion, doc_type: DocumentType) -> str:
    d = get_settings().docs_dir / "models" / mv.semantic_version
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{doc_type.value}.md"
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def write_document(
    db: Session, mv: ModelVersion, doc_type: DocumentType, content: str, status: str, actor: str
) -> Document:
    """Create or replace a version's document; bumps the document version and rewrites the file."""
    meta, body = parse_front_matter(content)
    meta["status"] = status
    meta["model_version"] = mv.semantic_version
    content = dump_document(meta, body)
    path = doc_path_for(mv, doc_type)
    (ROOT / path).write_text(content)
    doc = db.scalar(select(Document).where(Document.model_version_id == mv.id, Document.type == doc_type.value))
    before = None
    if doc is None:
        doc = Document(
            model_version_id=mv.id,
            type=doc_type.value,
            version=1,
            content_hash=sha256_text(content),
            status=status,
            path=path,
            content=content,
        )
        db.add(doc)
    else:
        before = {"version": doc.version, "content_hash": doc.content_hash, "status": doc.status}
        doc.version += 1
        doc.content = content
        doc.content_hash = sha256_text(content)
        doc.status = status
        doc.path = path
    db.flush()
    record_event(
        db,
        actor_id=actor,
        action="document.written",
        entity_type="document",
        entity_id=f"{mv.semantic_version}:{doc_type.value}",
        before=before,
        after={"version": doc.version, "content_hash": doc.content_hash, "status": status},
    )
    return doc


def render_all(
    db: Session, mv: ModelVersion, extra: dict[str, Any] | None, complete: bool, actor: str
) -> list[Document]:
    """Render every template with known facts (+ optional narrative context).

    Status is 'complete' only when the caller asks for it *and* the rendered document has no
    remaining placeholders; otherwise it stays 'draft'.
    """
    from modelguard_governance.documents import missing_sections

    ctx = {**base_context(db, mv), **(mv.measured_json or {}), **(mv.narrative_json or {}), **(extra or {})}
    ctx["status"] = "complete" if complete else "draft"
    docs = []
    for dt in DocumentType:
        content = render_template(dt, ctx)
        status = "complete" if complete and not missing_sections(dt, content) else "draft"
        docs.append(write_document(db, mv, dt, content, status, actor))
    return docs


def get_documents(db: Session, mv: ModelVersion) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.model_version_id == mv.id).order_by(Document.type)))


def update_document(
    db: Session, mv: ModelVersion, doc_type: DocumentType, content: str, status: str, user: User
) -> Document:
    doc = write_document(db, mv, doc_type, content, status, user.username)
    db.commit()
    return doc

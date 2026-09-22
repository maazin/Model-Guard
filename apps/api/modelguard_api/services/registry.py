"""Model registry: registration, validation, lifecycle transitions, controls, decisions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from modelguard_governance.documents import DocumentType, missing_sections
from modelguard_governance.lifecycle import Action, State, assert_role, is_modifiable, next_state
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api.errors import bad_request, conflict, not_found
from modelguard_api.models import (
    ApprovalDecision,
    Control,
    MetricResult,
    ModelVersion,
    TrainingRun,
    User,
    ValidationArtifact,
)
from modelguard_api.services import documents as docsvc
from modelguard_api.services.audit import record_event

SEMVER_RE = re.compile(r"^pd-credit-v\d+\.\d+\.\d+$")


def get_version(db: Session, ident: str) -> ModelVersion:
    mv = db.get(ModelVersion, ident) or db.scalar(select(ModelVersion).where(ModelVersion.semantic_version == ident))
    if mv is None:
        raise not_found("model version", ident)
    return mv


def _assert_modifiable(mv: ModelVersion) -> None:
    if not is_modifiable(mv.state):
        raise conflict(f"model version {mv.semantic_version} is in state {mv.state} and cannot be modified")


def register_version(
    db: Session, *, training_run_id: str, semantic_version: str, model_type: str, description: str, user: User
) -> ModelVersion:
    run = db.get(TrainingRun, training_run_id)
    if run is None:
        raise not_found("training run", training_run_id)
    if run.status != "COMPLETED":
        raise bad_request(f"training run status is {run.status}; only COMPLETED runs can be registered")
    if model_type not in ("baseline", "champion"):
        raise bad_request("model_type must be 'baseline' or 'champion'")
    if not SEMVER_RE.match(semantic_version):
        raise bad_request("semantic_version must look like pd-credit-v1.2.3")
    if db.scalar(select(ModelVersion).where(ModelVersion.semantic_version == semantic_version)):
        raise conflict(f"{semantic_version} already exists")
    mv = ModelVersion(
        semantic_version=semantic_version,
        training_run_id=run.id,
        state=State.DRAFT,
        artifact_uri=run.artifacts_json[f"{model_type}_model"],
        model_type=model_type,
        owner=user.username,
        description=description,
    )
    db.add(mv)
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action="model_version.registered",
        entity_type="model_version",
        entity_id=mv.id,
        after={
            "semantic_version": semantic_version,
            "state": mv.state,
            "training_run_id": run.id,
            "model_type": model_type,
        },
    )
    docsvc.render_all(db, mv, None, complete=False, actor=user.username)
    db.commit()
    return mv


# ---------- validation ----------


def _fmt(x: Any, nd: int = 4) -> str:
    return f"{x:.{nd}f}" if isinstance(x, int | float) else str(x)


def measured_context(mv: ModelVersion) -> dict[str, Any]:
    run = mv.training_run
    evals = run.metrics_json
    mine = evals[mv.model_type]
    other_type = "baseline" if mv.model_type == "champion" else "champion"
    other = evals[other_type]
    m, o = mine["metrics"], other["metrics"]

    def row(name: str, key: str) -> str:
        a, b = m[key], o[key]
        ci = f" [{_fmt(a['lower_ci'])}, {_fmt(a['upper_ci'])}]" if "lower_ci" in a else ""
        return f"| {name} | {_fmt(a['value'])}{ci} | {_fmt(b['value'])} |"

    discrimination = (
        f"| Metric | {mv.model_type} (registered) | {other_type} |\n| --- | --- | --- |\n"
        + "\n".join(
            [
                row("AUC-ROC (95% bootstrap CI)", "auc"),
                row("KS (95% bootstrap CI)", "ks"),
                row("Brier score", "brier"),
                row("ECE (10 bins)", "ece"),
            ]
        )
        + f"\n\nHoldout rows: {int(m['n_holdout']['value'])}; holdout default rate {_fmt(m['holdout_default_rate']['value'], 3)}. "
        "Interpretation: AUC/KS measure rank ordering; Brier/ECE measure probability quality. "
        f"Limitation: bootstrap resamples the temporal holdout only ({run.config_json.get('n_bootstrap')} draws); no cross-period stability claim. "
        f"Artifact: `artifacts/runs/{run.id}/metrics.json`. Reviewer status: pending."
    )
    cal = mine["calibration"]
    cal_rows = "\n".join(
        f"| {i + 1} | {n} | {_fmt(p, 3)} | {_fmt(o_, 3)} |"
        for i, (n, p, o_) in enumerate(zip(cal["bin_count"], cal["mean_predicted"], cal["observed_rate"], strict=True))
        if n > 0
    )
    calibration = (
        f"ECE = {_fmt(cal['ece'])} over 10 equal-width bins (configurable).\n\n| Bin | n | Mean predicted | Observed |\n| --- | --- | --- | --- |\n{cal_rows}\n\n"
        "Interpretation: bins near the diagonal indicate well-calibrated PDs. Limitation: sparse high-score bins are noisy. Reviewer status: pending."
    )
    conf = mine["confusion"]
    threshold = (
        f"Illustrative threshold {_fmt(conf['threshold'], 2)} (F1-optimal on validation; **not a lending policy**): "
        f"TP {conf['tp']}, FP {conf['fp']}, TN {conf['tn']}, FN {conf['fn']}; precision {_fmt(conf['precision'], 3)}, "
        f"recall {_fmt(conf['recall'], 3)}, selection rate {_fmt(conf['selection_rate'], 3)}. Full grid stored as the "
        "`threshold_analysis` artifact. Reviewer status: pending."
    )
    imp = mine["feature_importance"]
    importance = (
        "Permutation importance (AUC drop, 10 repeats; ADR-0005):\n\n| Feature | Mean | Std |\n| --- | --- | --- |\n"
        + "\n".join(f"| `{r['feature']}` | {_fmt(r['importance_mean'])} | {_fmt(r['importance_std'])} |" for r in imp)
        + "\n\nLimitation: permutation importance is confounded by correlated features. Reviewer status: pending."
    )
    ht = run.hypothesis_tests_json[0] if run.hypothesis_tests_json else None
    hypothesis = (
        f"Two-sample KS test on `{ht['feature']}` (train vs. temporal holdout): D = {_fmt(ht['statistic'])}, "
        f"p = {_fmt(ht['p_value'])}, Cohen's d = {_fmt(ht['effect_size']['cohens_d'])}, n = {ht['n_a']} / {ht['n_b']}. "
        f"H0 {'rejected' if ht['reject_null'] else 'not rejected'} at α = {ht['alpha']}. Assumptions: {', '.join(ht['assumptions'])}. "
        f"Limitation: {ht['limitation']} Reviewer status: pending."
        if ht
        else None
    )
    fair = mine.get("fairness")
    if fair:
        rows = "\n".join(
            f"| {g} | {v['n']} | {_fmt(v['selection_rate'], 3)} | {_fmt(v['tpr'], 3)} | {_fmt(v['fpr'], 3)} | {_fmt(v['observed_default_rate'], 3)} | {_fmt(v['mean_predicted'], 3)} |"
            for g, v in fair["groups"].items()
        )
        fairness = (
            f"Synthetic `fairness_group` cohorts at threshold {_fmt(fair['threshold'], 2)}: selection-rate ratio {_fmt(fair['selection_rate_ratio'], 3)}, "
            f"TPR difference {_fmt(fair['tpr_difference'], 3)}, FPR difference {_fmt(fair['fpr_difference'], 3)}.\n\n"
            "| Group | n | Selection rate | TPR | FPR | Observed default | Mean predicted |\n| --- | --- | --- | --- | --- | --- | --- |\n"
            f"{rows}\n\n{fair['disclaimer']} Reviewer status: pending."
        )
    else:
        fairness = "No grouping field available; see the risk assessment for the documented reason."
    cfg = run.config_json
    spec = cfg.get("feature_spec") or {}
    synthetic = "synthetic" in (spec.get("source_id") or run.snapshot.source_id)
    split_strategy = cfg.get("split", {}).get("strategy")
    fairness_field = spec.get("fairness_field") or "fairness_group"
    limitations = "\n".join(
        [
            "- Synthetic data; results do not transfer to any real portfolio."
            if synthetic
            else "- Public 2005 Taiwanese credit-card sample (UCI 350); results do not transfer to any other market, period or product.",
            "- Temporal split over a short window; macro regimes are not represented (ADR-0003)."
            if split_strategy == "temporal"
            else "- No valid time axis, so the split is stratified: there is no out-of-time performance estimate (ADR-0003).",
            f"- Holdout of {int(m['n_holdout']['value'])} rows; treat differences inside the bootstrap CI as noise.",
            "- The illustrative threshold is not a credit policy; no lending decision should be derived from it.",
            f"- Fairness diagnostics use the `{fairness_field}` field"
            + (" (synthetic cohort)" if synthetic else " (never a model feature)")
            + " and are not a legal determination.",
        ]
    )
    performance_summary = (
        f"Holdout AUC {_fmt(m['auc']['value'], 3)} [{_fmt(m['auc']['lower_ci'], 3)}, {_fmt(m['auc']['upper_ci'], 3)}], "
        f"KS {_fmt(m['ks']['value'], 3)}, Brier {_fmt(m['brier']['value'], 4)}, ECE {_fmt(m['ece']['value'], 4)} "
        f"versus {other_type} AUC {_fmt(o['auc']['value'], 3)}. Fairness: selection-rate ratio "
        f"{_fmt(fair['selection_rate_ratio'], 3) if fair else 'n/a'}. Full detail in the validation report."
    )
    monitoring_summary = (
        f"PSI on every feature and on scores against stored training distributions; defaults stable < {docsvc.PSI_INVESTIGATE}, "
        f"investigate {docsvc.PSI_INVESTIGATE}–{docsvc.PSI_ALERT}, alert > {docsvc.PSI_ALERT}; AUC drop > {docsvc.DEFAULT_AUC_DROP} when labels arrive. "
        "Configurable project defaults, not policy."
    )
    return {
        "discrimination_table": discrimination,
        "calibration_summary": calibration,
        "threshold_summary": threshold,
        "importance_table": importance,
        "hypothesis_summary": hypothesis,
        "fairness_summary": fairness,
        "limitations": limitations,
        "performance_summary": performance_summary,
        "monitoring_summary": monitoring_summary,
        "reviewer_status": "Pending human review. Approval state is tracked in the registry.",
    }


def validate_version(db: Session, mv: ModelVersion, user: User) -> ModelVersion:
    assert_role(user.role, Action.VALIDATE)
    new = next_state(mv.state, Action.VALIDATE)
    run = mv.training_run
    evals = run.metrics_json
    # Persist scalar metrics (registered model = 'holdout', comparator = 'holdout_comparator').
    db.query(MetricResult).filter(
        MetricResult.model_version_id == mv.id, MetricResult.scope.in_(["holdout", "holdout_comparator"])
    ).delete()
    for mt, ev in evals.items():
        scope = "holdout" if mt == mv.model_type else "holdout_comparator"
        for name, val in ev["metrics"].items():
            db.add(
                MetricResult(
                    model_version_id=mv.id,
                    scope=scope,
                    metric_name=name,
                    metric_value=val["value"],
                    lower_ci=val.get("lower_ci"),
                    upper_ci=val.get("upper_ci"),
                )
            )
    mine = evals[mv.model_type]
    artifacts: dict[str, Any] = {
        "roc": mine["roc"],
        "calibration": mine["calibration"],
        "threshold_analysis": mine["threshold_analysis"],
        "confusion": mine["confusion"],
        "feature_importance": mine["feature_importance"],
        "hypothesis_test": run.hypothesis_tests_json,
        "fairness": mine.get("fairness"),
        "baseline_distributions": run.baseline_distributions_json,
        "comparator": {k: v["metrics"] for k, v in evals.items()},
    }
    pred_path = (run.artifacts_json or {}).get("holdout_predictions")
    if pred_path and Path(pred_path).exists():
        artifacts["holdout_predictions"] = json.loads(Path(pred_path).read_text()).get(mv.model_type, {})
    db.query(ValidationArtifact).filter(ValidationArtifact.model_version_id == mv.id).delete()
    for name, payload in artifacts.items():
        if payload is not None:
            db.add(ValidationArtifact(model_version_id=mv.id, name=name, payload_json=payload))
    mv.measured_json = measured_context(mv)
    before = mv.state
    mv.state = new
    db.flush()
    docsvc.render_all(db, mv, None, complete=bool(mv.narrative_json), actor=user.username)
    record_event(
        db,
        actor_id=user.username,
        action="model_version.validated",
        entity_type="model_version",
        entity_id=mv.id,
        before={"state": before},
        after={"state": new, "holdout": mine["metrics"]},
    )
    db.commit()
    return mv


# ---------- documents / controls ----------


def set_narrative(db: Session, mv: ModelVersion, narrative: dict[str, Any], user: User) -> list[Any]:
    _assert_modifiable(mv)
    mv.narrative_json = {**(mv.narrative_json or {}), **narrative}
    db.flush()
    docs = docsvc.render_all(db, mv, None, complete=True, actor=user.username)
    record_event(
        db,
        actor_id=user.username,
        action="model_version.narrative_updated",
        entity_type="model_version",
        entity_id=mv.id,
        after={"keys": sorted(narrative)},
    )
    db.commit()
    return docs


def set_document_status(db: Session, mv: ModelVersion, doc_type: DocumentType, status: str, user: User) -> Any:
    _assert_modifiable(mv)
    doc = next((d for d in docsvc.get_documents(db, mv) if d.type == doc_type.value), None)
    if doc is None:
        raise not_found("document", doc_type.value)
    if status == "complete":
        gaps = missing_sections(doc_type, doc.content)
        if gaps:
            raise conflict(
                f"document {doc_type.value} still has placeholder sections", extra={"missing_sections": gaps}
            )
    return docsvc.update_document(db, mv, doc_type, doc.content, status, user)


def replace_controls(db: Session, mv: ModelVersion, controls: list[dict[str, Any]], user: User) -> list[Control]:
    _assert_modifiable(mv)
    db.query(Control).filter(Control.model_version_id == mv.id).delete()
    rows = [Control(model_version_id=mv.id, **c) for c in controls]
    db.add_all(rows)
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action="controls.replaced",
        entity_type="model_version",
        entity_id=mv.id,
        after={"controls": [c["control_name"] for c in controls]},
    )
    # Control matrix document is derived from the controls table.
    docsvc.render_all(db, mv, None, complete=bool(mv.narrative_json), actor=user.username)
    db.commit()
    return rows


def get_controls(db: Session, mv: ModelVersion) -> list[Control]:
    return list(db.scalars(select(Control).where(Control.model_version_id == mv.id).order_by(Control.control_name)))


# ---------- transitions ----------


def _transition(
    db: Session, mv: ModelVersion, action: Action, user: User, extra: dict[str, Any] | None = None
) -> ModelVersion:
    assert_role(user.role, action)
    before = mv.state
    mv.state = next_state(mv.state, action)
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action=f"model_version.{action.value}",
        entity_type="model_version",
        entity_id=mv.id,
        before={"state": before},
        after={"state": mv.state, **(extra or {})},
    )
    return mv


def submit_review(db: Session, mv: ModelVersion, user: User) -> ModelVersion:
    from modelguard_governance.readiness import blocking_for_review

    from modelguard_api.services.readiness import evaluate_and_store

    assert_role(user.role, Action.SUBMIT_REVIEW)
    next_state(mv.state, Action.SUBMIT_REVIEW)  # raises if not VALIDATED
    results = evaluate_and_store(db, mv)
    blocking = blocking_for_review(results)
    if blocking:
        record_event(
            db,
            actor_id=user.username,
            action="model_version.submit_review_blocked",
            entity_type="model_version",
            entity_id=mv.id,
            after={"blocking_checks": [b.check_name for b in blocking]},
        )
        db.commit()
        raise conflict(
            f"readiness gate blocked submission: {len(blocking)} check(s) failing",
            extra={"blocking": [b.to_dict() for b in blocking]},
        )
    _transition(db, mv, Action.SUBMIT_REVIEW, user)
    db.commit()
    return mv


def decide(db: Session, mv: ModelVersion, decision: str, rationale: str, user: User) -> ModelVersion:
    from modelguard_governance.readiness import blocking_for_approval

    from modelguard_api.services.readiness import evaluate_and_store

    if decision not in ("approve", "reject"):
        raise bad_request("decision must be 'approve' or 'reject'")
    if not rationale.strip():
        raise bad_request("rationale is required")
    action = Action.APPROVE if decision == "approve" else Action.REJECT
    assert_role(user.role, action)
    next_state(mv.state, action)
    if decision == "approve":
        blocking = blocking_for_approval(evaluate_and_store(db, mv))
        if blocking:
            raise conflict(
                "cannot approve: readiness checks are failing", extra={"blocking": [b.to_dict() for b in blocking]}
            )
    dec = ApprovalDecision(model_version_id=mv.id, reviewer_id=user.username, decision=decision, rationale=rationale)
    db.add(dec)
    _transition(db, mv, action, user, {"decision": decision, "rationale": rationale})
    evaluate_and_store(db, mv)  # refresh sign_off check
    db.commit()
    return mv


def start_monitoring(db: Session, mv: ModelVersion, user: User) -> ModelVersion:
    _transition(db, mv, Action.START_MONITORING, user)
    db.commit()
    return mv


def retire(db: Session, mv: ModelVersion, reason: str, user: User) -> ModelVersion:
    if not reason.strip():
        raise bad_request("a retirement reason is required")
    mv.retirement_reason = reason
    _transition(db, mv, Action.RETIRE, user, {"reason": reason})
    db.commit()
    return mv


def reopen(db: Session, mv: ModelVersion, user: User) -> ModelVersion:
    _transition(db, mv, Action.REOPEN, user)
    db.commit()
    return mv


def latest_decision(db: Session, mv: ModelVersion) -> ApprovalDecision | None:
    return db.scalar(
        select(ApprovalDecision)
        .where(ApprovalDecision.model_version_id == mv.id)
        .order_by(ApprovalDecision.decided_at.desc())
        .limit(1)
    )

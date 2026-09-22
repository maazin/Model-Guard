"""One-screen decision summary for a risk leader."""

from __future__ import annotations

from typing import Any

from modelguard_governance.lifecycle import State
from sqlalchemy.orm import Session

from modelguard_api.models import ModelVersion
from modelguard_api.services import monitoring as monsvc
from modelguard_api.services.readiness import evaluate_and_store

NEXT_ACTION = {
    State.DRAFT: "Run validation to produce holdout metrics and reports.",
    State.VALIDATED: "Complete documentation and controls, then submit for review.",
    State.PENDING_REVIEW: "Reviewer must approve or reject with a rationale.",
    State.APPROVED: "Evaluate the first dated monitoring batch.",
    State.MONITORING: "Work open alerts; resolve or escalate before the due date.",
    State.REJECTED: "Address the rejection rationale and reopen the draft.",
    State.RETIRED: "No action; version retired.",
}


def summary(db: Session, mv: ModelVersion) -> dict[str, Any]:
    run = mv.training_run
    holdout = run.metrics_json.get(mv.model_type, {}).get("metrics", {})
    comparator = run.metrics_json.get("baseline" if mv.model_type == "champion" else "champion", {}).get("metrics", {})
    checks = evaluate_and_store(db, mv)
    failing = [c for c in checks if not c.passed]
    batches = monsvc.batches_for(db, mv)
    alerts = monsvc.alerts_for(db, mv)
    open_alerts = [a for a in alerts if a.status != "resolved"]
    high = [a for a in open_alerts if a.severity == "high"]
    latest = batches[-1] if batches else None
    latest_perf = (latest.results_json.get("performance") if latest else None) or {}
    gaps = [c for c in failing if c.check_name != "sign_off"]
    if mv.state == State.RETIRED:
        health = "retired"
    elif high:
        health = "at_risk"
    elif open_alerts or gaps:
        health = "watch"
    else:
        health = "healthy"
    top_risks: list[str] = [
        a.title for a in sorted(open_alerts, key=lambda a: (a.severity != "high", a.created_at))[:3]
    ]
    top_risks += [f"Readiness gap: {c.check_name.replace('_', ' ')}" for c in failing[:3] if c.check_name != "sign_off"]
    if mv.state in (State.MONITORING,) and high:
        recommendation = (
            "Do not extend use; investigate high-severity drift alerts and consider re-training with recent data."
        )
    elif mv.state == State.PENDING_REVIEW:
        recommendation = "Review package is complete; reviewer decision required."
    elif failing and mv.state in (State.DRAFT, State.VALIDATED):
        recommendation = "Not ready: close readiness gaps before review."
    elif mv.state in (State.APPROVED, State.MONITORING):
        recommendation = "Continue use under quarterly monitoring; no material alerts open."
    else:
        recommendation = NEXT_ACTION[State(mv.state)]
    return {
        "model_version": mv.semantic_version,
        "model_version_id": mv.id,
        "state": mv.state,
        "model_type": mv.model_type,
        "purpose": (mv.narrative_json or {}).get("business_purpose")
        or "Probability-of-default scoring for portfolio risk ranking. Portfolio simulation; not a lending decision engine.",
        "limits": [
            "Not credit advice: the cut-off shown is illustrative, not a lending policy.",
            "Built on a public sample or synthetic data; results do not transfer to a real portfolio.",
            "Fairness figures are for discussion, not a legal determination.",
            "Approval here is a simulated governance step, not regulatory compliance.",
        ],
        "health": health,
        "holdout": {k: v for k, v in holdout.items() if k in ("auc", "ks", "brier", "ece")},
        "comparator": {k: v for k, v in comparator.items() if k in ("auc", "ks", "brier", "ece")},
        "latest_batch": {
            "as_of_date": latest.as_of_date,
            "status": latest.status,
            "auc": latest_perf.get("auc", {}).get("value"),
            "labels_available": latest.labels_available,
        }
        if latest
        else None,
        "batches_evaluated": len(batches),
        "alerts": {"open": len(open_alerts), "high": len(high), "resolved": len(alerts) - len(open_alerts)},
        "readiness": {
            "passed": len(checks) - len(failing),
            "total": len(checks),
            "failing": [c.check_name for c in failing],
        },
        "top_risks": top_risks[:5],
        "recommendation": recommendation,
        "next_action": NEXT_ACTION[State(mv.state)],
    }

"""Deterministic readiness engine.

Given an evidence snapshot assembled from the registry, returns *every* unmet requirement with
the specific missing evidence, never a bare pass/fail. The engine has no I/O so each blocking
condition is unit-testable in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from modelguard_governance.documents import DocumentType, missing_sections

REQUIRED_HOLDOUT_METRICS = ("auc", "ks", "brier", "ece")
REQUIRED_VALIDATION_ARTIFACTS = ("calibration", "threshold_analysis", "feature_importance", "hypothesis_test")
REQUIRED_CONTROL_FIELDS = ("owner", "frequency", "evidence_uri", "status")
COMPLETE_CONTROL_STATUSES = frozenset({"implemented", "tested", "effective"})
MIN_CONTROLS = 3

CHECK_NAMES = (
    "dataset_lineage",
    "model_documentation",
    "validation",
    "monitoring_plan",
    "fairness_assessment",
    "controls",
    "security",
    "sign_off",
)
# Sign-off is recorded by the reviewer decision, so it is not required to *enter* review.
CHECKS_REQUIRED_FOR_REVIEW = tuple(c for c in CHECK_NAMES if c != "sign_off")


@dataclass
class ReadinessEvidence:
    source: dict[str, Any] | None = None
    snapshot: dict[str, Any] | None = None
    documents: dict[str, dict[str, Any]] = field(default_factory=dict)
    holdout_metrics: set[str] = field(default_factory=set)
    validation_artifacts: set[str] = field(default_factory=set)
    monitoring_plan: dict[str, Any] | None = None
    has_baseline_distributions: bool = False
    fairness_metrics_present: bool = False
    fairness_unavailable_reason: str | None = None
    controls: list[dict[str, Any]] = field(default_factory=list)
    security: dict[str, Any] = field(default_factory=dict)
    signoff: dict[str, Any] | None = None


@dataclass
class CheckResult:
    check_name: str
    status: str  # "pass" | "fail"
    missing: list[str]
    evidence: dict[str, Any]

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "missing": self.missing,
            "evidence": self.evidence,
        }


def _result(name: str, missing: list[str], evidence: dict[str, Any]) -> CheckResult:
    return CheckResult(name, "pass" if not missing else "fail", missing, evidence)


def _doc_missing(ev: ReadinessEvidence, doc_type: DocumentType, label: str) -> list[str]:
    doc = ev.documents.get(doc_type.value)
    if doc is None:
        return [f"{label} document is missing"]
    out: list[str] = []
    if doc.get("status") != "complete":
        out.append(f"{label} document has not been marked complete (currently '{doc.get('status')}')")
    gaps = missing_sections(doc_type, doc.get("content", ""))
    out.extend(f"{label}: the section '{s}' has not been written" for s in gaps)
    return out


def check_dataset_lineage(ev: ReadinessEvidence) -> CheckResult:
    missing: list[str] = []
    src = ev.source or {}
    if not ev.source:
        missing.append("no data source has been registered")
    else:
        for key, label in (
            ("id", "source ID"),
            ("doc_path", "source document (data_sources/<id>.md)"),
            ("retrieval_date", "retrieval date"),
            ("license_url", "license URL"),
        ):
            if not src.get(key):
                missing.append(f"{label} missing on data source")
    snap = ev.snapshot or {}
    if not ev.snapshot:
        missing.append("no data snapshot is linked to this version")
    else:
        if not snap.get("checksum"):
            missing.append("the data snapshot has no checksum")
        if snap.get("quality_status") not in ("pass", "warn"):
            missing.append(f"the data-quality check did not pass (result: {snap.get('quality_status')})")
    missing.extend(_doc_missing(ev, DocumentType.DATA_LINEAGE, "Data lineage / dictionary"))
    return _result("dataset_lineage", missing, {"source": src.get("id"), "snapshot_checksum": snap.get("checksum")})


def check_model_documentation(ev: ReadinessEvidence) -> CheckResult:
    missing = _doc_missing(ev, DocumentType.MODEL_CARD, "Model card")
    missing += _doc_missing(ev, DocumentType.INTENDED_USE, "Intended-use statement")
    return _result("model_documentation", missing, {"documents": sorted(ev.documents)})


def check_validation(ev: ReadinessEvidence) -> CheckResult:
    missing = [
        f"test result '{m}' has not been recorded" for m in REQUIRED_HOLDOUT_METRICS if m not in ev.holdout_metrics
    ]
    missing += [
        f"validation artifact '{a}' missing" for a in REQUIRED_VALIDATION_ARTIFACTS if a not in ev.validation_artifacts
    ]
    missing += _doc_missing(ev, DocumentType.VALIDATION_REPORT, "Validation report")
    return _result(
        "validation",
        missing,
        {"metrics": sorted(ev.holdout_metrics), "artifacts": sorted(ev.validation_artifacts)},
    )


def check_monitoring_plan(ev: ReadinessEvidence) -> CheckResult:
    missing = _doc_missing(ev, DocumentType.MONITORING_PLAN, "Monitoring plan")
    plan = ev.monitoring_plan or {}
    if not ev.has_baseline_distributions:
        missing.append("reference distributions for drift checks have not been stored")
    if not plan.get("psi_bins"):
        missing.append("the monitoring plan does not say how many bins the drift check uses")
    thresholds = plan.get("alert_thresholds") or {}
    for key in ("psi_investigate", "psi_alert", "auc_drop"):
        if key not in thresholds:
            missing.append(f"the monitoring plan does not set the alert threshold '{key}'")
    if not plan.get("owner"):
        missing.append("the monitoring plan names no owner")
    return _result("monitoring_plan", missing, {"plan": plan})


def check_fairness_assessment(ev: ReadinessEvidence) -> CheckResult:
    missing: list[str] = []
    if ev.fairness_metrics_present:
        missing += _doc_missing(ev, DocumentType.RISK_ASSESSMENT, "AI/model risk assessment")
    elif not ev.fairness_unavailable_reason:
        missing.append("no fairness metrics recorded and no documented reason the grouping field is unavailable")
    return _result(
        "fairness_assessment",
        missing,
        {"metrics_present": ev.fairness_metrics_present, "unavailable_reason": ev.fairness_unavailable_reason},
    )


def check_controls(ev: ReadinessEvidence) -> CheckResult:
    missing = _doc_missing(ev, DocumentType.CONTROL_MATRIX, "Risk-control matrix")
    if len(ev.controls) < MIN_CONTROLS:
        missing.append(f"only {len(ev.controls)} controls are recorded; at least {MIN_CONTROLS} required")
    for c in ev.controls:
        name = c.get("control_name", "<unnamed>")
        for f in REQUIRED_CONTROL_FIELDS:
            if not c.get(f):
                missing.append(f"control '{name}' has no {f.replace('_', ' ')}")
        if c.get("status") and c["status"] not in COMPLETE_CONTROL_STATUSES:
            missing.append(f"control '{name}' is still '{c['status']}', not implemented or tested")
    return _result("controls", missing, {"controls": [c.get("control_name") for c in ev.controls]})


def check_security(ev: ReadinessEvidence) -> CheckResult:
    missing: list[str] = []
    if ev.security.get("secrets_scan") != "pass":
        missing.append(f"the secrets scan has not passed (result: {ev.security.get('secrets_scan')})")
    if ev.security.get("raw_rows_in_logs", True):
        missing.append("borrower-level records were found, or not verified absent, in documents or prompts")
    return _result("security", missing, dict(ev.security))


def check_sign_off(ev: ReadinessEvidence) -> CheckResult:
    missing: list[str] = []
    so = ev.signoff or {}
    if not ev.signoff:
        missing.append("no reviewer decision has been recorded")
    else:
        if so.get("decision") != "approve":
            missing.append(f"the latest reviewer decision was '{so.get('decision')}', not approval")
        if not so.get("rationale"):
            missing.append("the reviewer gave no reason")
        if not so.get("reviewer_id"):
            missing.append("the reviewer is not identified")
    return _result("sign_off", missing, so)


CHECKS = {
    "dataset_lineage": check_dataset_lineage,
    "model_documentation": check_model_documentation,
    "validation": check_validation,
    "monitoring_plan": check_monitoring_plan,
    "fairness_assessment": check_fairness_assessment,
    "controls": check_controls,
    "security": check_security,
    "sign_off": check_sign_off,
}


def evaluate(ev: ReadinessEvidence) -> list[CheckResult]:
    return [CHECKS[name](ev) for name in CHECK_NAMES]


def blocking_for_review(results: list[CheckResult]) -> list[CheckResult]:
    return [r for r in results if r.check_name in CHECKS_REQUIRED_FOR_REVIEW and not r.passed]


def blocking_for_approval(results: list[CheckResult]) -> list[CheckResult]:
    """Approval requires everything except sign_off (the approval *is* the sign-off)."""
    return blocking_for_review(results)

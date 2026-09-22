import pytest

from modelguard_governance.documents import DocumentType
from modelguard_governance.readiness import (
    CHECK_NAMES,
    ReadinessEvidence,
    blocking_for_review,
    evaluate,
)

_SECTION_BODY = {
    DocumentType.INTENDED_USE: "Business purpose\nIntended use\nOut-of-scope uses\nUsers and decisions",
}


def complete_doc(doc_type: DocumentType) -> dict:
    from modelguard_governance.documents import REQUIRED_SECTIONS

    body = "\n\n".join(f"## {s}\n\nContent for {s}." for s in REQUIRED_SECTIONS[doc_type])
    return {"status": "complete", "content": f"---\nstatus: complete\n---\n\n{body}"}


def complete_evidence() -> ReadinessEvidence:
    return ReadinessEvidence(
        source={"id": "src", "doc_path": "docs/data-sources/src.md", "retrieval_date": "2026-01-01", "license_url": "https://x"},
        snapshot={"checksum": "abc", "quality_status": "pass"},
        documents={t.value: complete_doc(t) for t in DocumentType},
        holdout_metrics={"auc", "ks", "brier", "ece"},
        validation_artifacts={"calibration", "threshold_analysis", "feature_importance", "hypothesis_test"},
        monitoring_plan={"psi_bins": 10, "alert_thresholds": {"psi_investigate": 0.1, "psi_alert": 0.25, "auc_drop": 0.05}, "owner": "ds"},
        has_baseline_distributions=True,
        fairness_metrics_present=True,
        controls=[
            {"control_name": f"c{i}", "owner": "o", "frequency": "monthly", "evidence_uri": "x", "status": "implemented"}
            for i in range(3)
        ],
        security={"secrets_scan": "pass", "raw_rows_in_logs": False},
        signoff={"reviewer_id": "rev", "decision": "approve", "rationale": "ok"},
    )


def _failing(results):
    return {r.check_name: r for r in results if not r.passed}


def test_complete_evidence_passes_all_checks():
    results = evaluate(complete_evidence())
    assert [r.check_name for r in results] == list(CHECK_NAMES)
    assert all(r.passed for r in results)
    assert blocking_for_review(results) == []


def test_sign_off_not_required_for_review():
    ev = complete_evidence()
    ev.signoff = None
    results = evaluate(ev)
    assert _failing(results).keys() == {"sign_off"}
    assert blocking_for_review(results) == []


def test_missing_source_blocks_lineage():
    ev = complete_evidence()
    ev.source = None
    f = _failing(evaluate(ev))
    assert "dataset_lineage" in f and "data source not registered" in f["dataset_lineage"].missing


def test_failed_quality_run_blocks_lineage():
    ev = complete_evidence()
    ev.snapshot["quality_status"] = "fail"
    assert "dataset_lineage" in _failing(evaluate(ev))


def test_missing_model_card_blocks_documentation():
    ev = complete_evidence()
    del ev.documents["model_card"]
    f = _failing(evaluate(ev))
    assert "Model card document is missing" in f["model_documentation"].missing


def test_placeholder_section_blocks_documentation():
    ev = complete_evidence()
    ev.documents["model_card"]["content"] = ev.documents["model_card"]["content"].replace(
        "Content for Known limitations and failure modes.", "TODO"
    )
    f = _failing(evaluate(ev))
    assert any("Known limitations" in m for m in f["model_documentation"].missing)


def test_draft_status_blocks_documentation():
    ev = complete_evidence()
    ev.documents["model_card"]["status"] = "draft"
    assert "model_documentation" in _failing(evaluate(ev))


@pytest.mark.parametrize("metric", ["auc", "ks", "brier", "ece"])
def test_missing_metric_blocks_validation(metric):
    ev = complete_evidence()
    ev.holdout_metrics.discard(metric)
    f = _failing(evaluate(ev))
    assert f"holdout metric '{metric}' not recorded" in f["validation"].missing


@pytest.mark.parametrize("artifact", ["calibration", "threshold_analysis", "feature_importance", "hypothesis_test"])
def test_missing_artifact_blocks_validation(artifact):
    ev = complete_evidence()
    ev.validation_artifacts.discard(artifact)
    assert "validation" in _failing(evaluate(ev))


def test_missing_baseline_distributions_blocks_monitoring():
    ev = complete_evidence()
    ev.has_baseline_distributions = False
    f = _failing(evaluate(ev))
    assert any("baseline" in m for m in f["monitoring_plan"].missing)


def test_missing_threshold_blocks_monitoring():
    ev = complete_evidence()
    del ev.monitoring_plan["alert_thresholds"]["auc_drop"]
    f = _failing(evaluate(ev))
    assert any("auc_drop" in m for m in f["monitoring_plan"].missing)


def test_missing_owner_blocks_monitoring():
    ev = complete_evidence()
    ev.monitoring_plan["owner"] = ""
    assert "monitoring_plan" in _failing(evaluate(ev))


def test_fairness_requires_metrics_or_reason():
    ev = complete_evidence()
    ev.fairness_metrics_present = False
    assert "fairness_assessment" in _failing(evaluate(ev))
    ev.fairness_unavailable_reason = "grouping field not licensed"
    assert "fairness_assessment" not in _failing(evaluate(ev))


def test_too_few_controls_blocks():
    ev = complete_evidence()
    ev.controls = ev.controls[:2]
    assert "controls" in _failing(evaluate(ev))


def test_control_missing_owner_blocks():
    ev = complete_evidence()
    ev.controls[0]["owner"] = ""
    f = _failing(evaluate(ev))
    assert "control 'c0' missing owner" in f["controls"].missing


def test_control_not_implemented_blocks():
    ev = complete_evidence()
    ev.controls[1]["status"] = "planned"
    assert "controls" in _failing(evaluate(ev))


def test_secrets_scan_failure_blocks_security():
    ev = complete_evidence()
    ev.security["secrets_scan"] = "fail"
    assert "security" in _failing(evaluate(ev))


def test_raw_rows_in_logs_blocks_security():
    ev = complete_evidence()
    ev.security["raw_rows_in_logs"] = True
    assert "security" in _failing(evaluate(ev))


def test_reject_decision_fails_sign_off():
    ev = complete_evidence()
    ev.signoff = {"reviewer_id": "rev", "decision": "reject", "rationale": "no"}
    assert "sign_off" in _failing(evaluate(ev))


def test_empty_evidence_reports_every_gap():
    results = evaluate(ReadinessEvidence())
    assert all(not r.passed for r in results)
    assert sum(len(r.missing) for r in results) > 20

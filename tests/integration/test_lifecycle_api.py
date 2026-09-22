"""Import -> train -> validate -> register -> submit -> approve -> monitor, through the HTTP API."""

from __future__ import annotations

import pytest
from modelguard_api.seed import CONTROLS, NARRATIVE

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def snapshot(client, ds, source):
    r = client.post(
        "/api/v1/snapshots/import",
        json={"source_id": source["id"], "file_path": "data/fixtures/synthetic_loans.csv", "as_of_date": "2023-12-31"},
        headers=ds,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["quality_status"] == "pass" and len(body["checksum"]) == 64
    assert "target" in body["profile_json"]
    return body


@pytest.fixture(scope="module")
def run(client, ds, snapshot):
    r = client.post("/api/v1/training-runs", json={"snapshot_id": snapshot["id"], "random_seed": 42}, headers=ds)
    assert r.status_code == 202, r.text
    run = client.get(f"/api/v1/training-runs/{r.json()['id']}", headers=ds).json()
    assert run["status"] == "COMPLETED", run.get("error")
    assert run["config_json"]["random_seed"] == 42
    assert run["config_json"]["training_data_checksum"] == snapshot["checksum"]
    assert set(run["metrics_json"]) == {"baseline", "champion"}
    return run


@pytest.fixture(scope="module")
def version(client, ds, run):
    r = client.post(
        "/api/v1/model-versions",
        json={"training_run_id": run["id"], "semantic_version": "pd-credit-v9.0.0", "model_type": "champion"},
        headers=ds,
    )
    assert r.status_code == 201, r.text
    assert r.json()["state"] == "DRAFT"
    return r.json()


def test_snapshot_lineage_and_quality(client, ds, snapshot):
    r = client.get(f"/api/v1/snapshots/{snapshot['id']}", headers=ds)
    assert r.status_code == 200 and r.json()["source_id"] == "synthetic-loans-v1"


def test_training_is_reproducible_via_api(client, ds, snapshot, run):
    r = client.post("/api/v1/training-runs", json={"snapshot_id": snapshot["id"], "random_seed": 42}, headers=ds)
    again = client.get(f"/api/v1/training-runs/{r.json()['id']}", headers=ds).json()
    assert again["metrics_json"]["champion"]["metrics"] == run["metrics_json"]["champion"]["metrics"]


def test_reviewer_cannot_start_training(client, reviewer, snapshot):
    r = client.post("/api/v1/training-runs", json={"snapshot_id": snapshot["id"]}, headers=reviewer)
    assert r.status_code == 403
    assert r.headers["content-type"].startswith("application/problem+json")


def test_training_config_is_immutable_after_registration(client, ds, reviewer, run, version):
    for hdr in (ds, reviewer):
        assert client.put(f"/api/v1/training-runs/{run['id']}", json={"random_seed": 1}, headers=hdr).status_code == 405
        assert (
            client.patch(f"/api/v1/training-runs/{run['id']}", json={"random_seed": 1}, headers=hdr).status_code == 405
        )


def test_validate_and_readiness_gaps(client, ds, version):
    assert client.post(f"/api/v1/model-versions/{version['id']}/submit-review", headers=ds).status_code == 409  # DRAFT
    r = client.post(f"/api/v1/model-versions/{version['id']}/validate", headers=ds)
    assert r.status_code == 200 and r.json()["state"] == "VALIDATED"
    detail = client.get(f"/api/v1/model-versions/{version['id']}", headers=ds).json()
    names = {m["metric_name"] for m in detail["metrics"] if m["scope"] == "holdout"}
    assert {"auc", "ks", "brier", "ece"} <= names
    assert {"roc", "calibration", "threshold_analysis", "feature_importance", "hypothesis_test", "fairness"} <= set(
        detail["artifacts"]
    )
    failing = {c["check_name"]: c for c in detail["readiness"] if c["status"] == "fail"}
    assert {"model_documentation", "monitoring_plan", "controls", "fairness_assessment"} <= set(failing)


def test_submit_blocked_with_named_reasons(client, ds, version):
    r = client.post(f"/api/v1/model-versions/{version['id']}/submit-review", headers=ds)
    assert r.status_code == 409
    body = r.json()
    assert body["type"] == "urn:modelguard:conflict"
    blocking = {b["check_name"]: b["missing"] for b in body["blocking"]}
    assert len(blocking) >= 3 and all(blocking.values())


def test_complete_package_and_submit(client, ds, version):
    r = client.put(f"/api/v1/model-versions/{version['id']}/narrative", json={"narrative": NARRATIVE}, headers=ds)
    assert r.status_code == 200
    statuses = {d["type"]: d["status"] for d in r.json()}
    assert statuses["intended_use"] == "complete" and statuses["control_matrix"] == "draft"  # no controls yet
    r = client.put(f"/api/v1/model-versions/{version['id']}/controls", json=CONTROLS, headers=ds)
    assert r.status_code == 200 and len(r.json()) == len(CONTROLS)
    docs = client.get(f"/api/v1/model-versions/{version['id']}", headers=ds).json()["documents"]
    assert all(d["status"] == "complete" for d in docs), [(d["type"], d["status"]) for d in docs]
    r = client.post(f"/api/v1/model-versions/{version['id']}/submit-review", headers=ds)
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "PENDING_REVIEW"


def test_pending_review_is_frozen(client, ds, reviewer, version):
    assert client.put(f"/api/v1/model-versions/{version['id']}/controls", json=CONTROLS, headers=ds).status_code == 409
    assert (
        client.put(f"/api/v1/model-versions/{version['id']}/controls", json=CONTROLS, headers=reviewer).status_code
        == 403
    )
    assert (
        client.put(f"/api/v1/model-versions/{version['id']}/narrative", json={"narrative": {}}, headers=ds).status_code
        == 409
    )


def test_data_scientist_cannot_approve(client, ds, risk_leader, version):
    for hdr in (ds, risk_leader):
        r = client.post(
            f"/api/v1/model-versions/{version['id']}/decision",
            json={"decision": "approve", "rationale": "please"},
            headers=hdr,
        )
        assert r.status_code == 403, r.text


def test_reviewer_approves_and_audit_records_it(client, reviewer, version):
    r = client.post(
        f"/api/v1/model-versions/{version['id']}/decision",
        json={"decision": "approve", "rationale": "Package complete."},
        headers=reviewer,
    )
    assert r.status_code == 200 and r.json()["state"] == "APPROVED"
    events = client.get(f"/api/v1/audit-events?entity_id={version['id']}", headers=reviewer).json()
    actions = [e["action"] for e in events]
    assert "model_version.registered" in actions and "model_version.validated" in actions
    assert "model_version.submit_review_blocked" in actions and "model_version.approve" in actions
    assert client.get("/api/v1/audit-events/verify", headers=reviewer).json()["valid"] is True
    detail = client.get(f"/api/v1/model-versions/{version['id']}", headers=reviewer).json()
    assert all(c["status"] == "pass" for c in detail["readiness"])


def test_monitoring_with_drift_creates_alert_and_resolution_trail(client, ds, reviewer, source, version):
    stable = client.post(
        "/api/v1/snapshots/import",
        json={
            "source_id": source["id"],
            "file_path": "data/fixtures/monitoring/batch_2024-03-31.csv",
            "as_of_date": "2024-03-31",
            "purpose": "monitoring",
        },
        headers=ds,
    ).json()
    drifted = client.post(
        "/api/v1/snapshots/import",
        json={
            "source_id": source["id"],
            "file_path": "data/fixtures/monitoring/batch_2024-09-30.csv",
            "as_of_date": "2024-09-30",
            "purpose": "monitoring",
        },
        headers=ds,
    ).json()
    r = client.post(
        f"/api/v1/model-versions/{version['id']}/monitoring-batches", json={"snapshot_id": stable["id"]}, headers=ds
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "ok"
    assert client.get(f"/api/v1/model-versions/{version['id']}", headers=ds).json()["state"] == "MONITORING"
    r = client.post(
        f"/api/v1/model-versions/{version['id']}/monitoring-batches", json={"snapshot_id": drifted["id"]}, headers=ds
    )
    assert r.status_code == 201 and r.json()["status"] == "alert"
    psi = r.json()["results_json"]["psi"]
    assert psi["debt_to_income"]["status"] == "alert"
    mon = client.get(f"/api/v1/model-versions/{version['id']}/monitoring", headers=ds).json()
    high = [a for a in mon["alerts"] if a["severity"] == "high" and a["type"] == "psi"]
    assert high, mon["alerts"]
    alert = high[0]
    r = client.patch(
        f"/api/v1/model-versions/{version['id']}/alerts/{alert['id']}", json={"status": "resolved"}, headers=ds
    )
    assert r.status_code == 400  # note required
    r = client.patch(
        f"/api/v1/model-versions/{version['id']}/alerts/{alert['id']}",
        json={"status": "investigating", "note": "checking"},
        headers=ds,
    )
    assert r.status_code == 200 and r.json()["status"] == "investigating"
    r = client.patch(
        f"/api/v1/model-versions/{version['id']}/alerts/{alert['id']}",
        json={"status": "resolved", "note": "retrain scheduled"},
        headers=reviewer,
    )
    assert r.status_code == 200 and r.json()["resolution_note"] == "retrain scheduled"
    trail = [e["action"] for e in client.get(f"/api/v1/audit-events?entity_id={alert['id']}", headers=ds).json()]
    assert trail == ["alert.created", "alert.investigating", "alert.resolved"]
    assert client.get("/api/v1/audit-events/verify", headers=ds).json()["valid"] is True


def test_executive_summary_and_portfolio(client, risk_leader, version):
    r = client.get(f"/api/v1/executive-summary/{version['id']}", headers=risk_leader)
    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "MONITORING" and body["health"] == "at_risk" and body["recommendation"]
    assert "auc" in body["holdout"]
    assert client.get("/api/v1/portfolio", headers=risk_leader).json()["versions"]


def test_copilot_grounded_answer(client, risk_leader, version):
    r = client.post(
        f"/api/v1/model-versions/{version['id']}/copilot/query",
        json={"question": "What evidence is missing before approval? limitations monitoring"},
        headers=risk_leader,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "rule_based" and body["response"]["citations"]
    assert body["response"]["disclaimer"].startswith("Portfolio governance assistant")
    assert "ln_" not in body["response"]["answer"]


def test_documents_render_and_download(client, ds, version):
    r = client.get(f"/api/v1/model-versions/{version['id']}/documents/model_card", headers=ds)
    assert r.status_code == 200 and "## Known limitations and failure modes" in r.json()["content"]
    r = client.get(f"/api/v1/model-versions/{version['id']}/documents/validation_report/download", headers=ds)
    assert r.status_code == 200 and r.headers["content-disposition"].startswith("attachment")


def test_retire_requires_reason_and_reviewer(client, ds, reviewer, version):
    assert (
        client.post(
            f"/api/v1/model-versions/{version['id']}/retire", json={"reason": "obsolete"}, headers=ds
        ).status_code
        == 403
    )
    r = client.post(
        f"/api/v1/model-versions/{version['id']}/retire", json={"reason": "superseded by v9.1.0"}, headers=reviewer
    )
    assert r.status_code == 200 and r.json()["state"] == "RETIRED"

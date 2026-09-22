import pytest

pytestmark = pytest.mark.integration


def test_missing_user_header_is_401_problem(client):
    client.headers.pop("X-Demo-User", None)
    r = client.get("/api/v1/model-versions")
    assert r.status_code == 401
    assert r.headers["content-type"].startswith("application/problem+json")
    assert r.json()["type"] == "urn:modelguard:unauthenticated"


def test_unknown_version_is_404_problem(client, ds):
    r = client.get("/api/v1/model-versions/pd-credit-v0.0.0", headers=ds)
    assert r.status_code == 404 and r.json()["title"] == "Not found" and r.json()["instance"]


def test_validation_error_is_422_problem(client, ds):
    r = client.post("/api/v1/snapshots/import", json={"source_id": "x"}, headers=ds)
    assert r.status_code == 422 and r.json()["errors"]


def test_import_outside_data_dir_is_rejected(client, ds, source):
    r = client.post(
        "/api/v1/snapshots/import",
        json={"source_id": source["id"], "file_path": "/etc/passwd", "as_of_date": "2024-01-01"},
        headers=ds,
    )
    assert r.status_code == 400


def test_health_and_openapi(client):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from modelguard_api.db import Base, engine
from modelguard_api.main import app
from modelguard_api.seed import SOURCE, seed_users


@pytest.fixture(scope="session")
def client() -> TestClient:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    from modelguard_api.db import SessionLocal

    with SessionLocal() as db:
        seed_users(db)
    return TestClient(app)


def as_user(client: TestClient, username: str) -> TestClient:
    client.headers["X-Demo-User"] = username
    return client


@pytest.fixture(scope="session")
def ds(client: TestClient) -> dict[str, str]:
    return {"X-Demo-User": "data_scientist"}


@pytest.fixture(scope="session")
def reviewer() -> dict[str, str]:
    return {"X-Demo-User": "reviewer"}


@pytest.fixture(scope="session")
def risk_leader() -> dict[str, str]:
    return {"X-Demo-User": "risk_leader"}


@pytest.fixture(scope="session")
def source(client: TestClient, ds: dict[str, str]) -> dict:
    r = client.post("/api/v1/data-sources", json=SOURCE, headers=ds)
    assert r.status_code == 201, r.text
    return r.json()

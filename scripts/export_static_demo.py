"""Export the seeded API responses as static JSON for the read-only public demo (GitHub Pages).

Every GET the dashboard makes is captured under apps/web/public/demo-data/<path>.json; the copilot
answer for each version's default question is precomputed. No borrower-level rows are exported —
the API never returns them. Run after `make seed`.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("apps/api", "packages/ml", "packages/governance", "packages/shared"):
    sys.path.insert(0, str(ROOT / p))

from fastapi.testclient import TestClient  # noqa: E402
from modelguard_api.main import app  # noqa: E402
from modelguard_governance.documents import DocumentType  # noqa: E402

OUT = ROOT / "apps" / "web" / "public" / "demo-data"
HEADERS = {"X-Demo-User": "reviewer"}


def write(path: str, payload: object) -> None:
    target = OUT / (path.strip("/") + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, separators=(",", ":"), default=str))


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    client = TestClient(app, headers=HEADERS)
    get = lambda path: client.get(f"/api/v1{path}").json()  # noqa: E731
    versions = get("/model-versions")
    write("/portfolio", get("/portfolio"))
    write("/model-versions", versions)
    write("/users", get("/users"))
    write("/audit-events/verify", get("/audit-events/verify"))
    write("/audit-events", get("/audit-events?limit=1000"))
    for v in versions:
        sv = v["semantic_version"]
        for ident in (sv, v["id"]):
            write(f"/model-versions/{ident}", get(f"/model-versions/{sv}"))
            write(f"/model-versions/{ident}/monitoring", get(f"/model-versions/{sv}/monitoring"))
            write(f"/executive-summary/{ident}", get(f"/executive-summary/{sv}"))
            write(f"/model-versions/{ident}/readiness", get(f"/model-versions/{sv}/readiness"))
            sim = client.get(f"/api/v1/model-versions/{sv}/simulator")
            if sim.status_code == 200:
                write(f"/model-versions/{ident}/simulator", sim.json())
            for dt in DocumentType:
                write(
                    f"/model-versions/{ident}/documents/{dt.value}", get(f"/model-versions/{sv}/documents/{dt.value}")
                )
            q = f"What evidence is missing before {sv} can move to approved?"
            r = client.post(f"/api/v1/model-versions/{sv}/copilot/query", json={"question": q}).json()
            r["precomputed_question"] = q
            write(f"/model-versions/{ident}/copilot/query", r)
    count = sum(1 for _ in OUT.rglob("*.json"))
    size = sum(p.stat().st_size for p in OUT.rglob("*.json")) / 1e6
    print(f"exported {count} files ({size:.1f} MB) to {OUT.relative_to(ROOT)}")
    leaked = [p for p in OUT.rglob("*.json") if "ln_" in p.read_text() and '"loan_id"' in p.read_text()]
    assert not leaked, f"borrower-level rows found in export: {leaked}"


if __name__ == "__main__":
    main()

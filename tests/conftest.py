from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("apps/api", "packages/ml", "packages/governance", "packages/shared"):
    sys.path.insert(0, str(ROOT / p))

import os  # noqa: E402
import tempfile  # noqa: E402

# Isolate every test session: throwaway SQLite DB, artifact and docs directories.
_TMP = Path(tempfile.mkdtemp(prefix="modelguard-tests-"))
os.environ.setdefault("MODELGUARD_DATABASE_URL", f"sqlite:///{_TMP / 'test.db'}")
os.environ.setdefault("MODELGUARD_ARTIFACT_DIR", str(_TMP / "artifacts"))
os.environ.setdefault("MODELGUARD_DOCS_DIR", str(_TMP / "docs"))
os.environ.setdefault("MODELGUARD_N_BOOTSTRAP", "40")

import pytest  # noqa: E402

FIXTURE_CSV = ROOT / "data" / "fixtures" / "synthetic_loans.csv"
MONITORING_DIR = ROOT / "data" / "fixtures" / "monitoring"


@pytest.fixture(scope="session")
def fixture_csv() -> Path:
    return FIXTURE_CSV


@pytest.fixture(scope="session")
def monitoring_dir() -> Path:
    return MONITORING_DIR

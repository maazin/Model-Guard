"""Fail if the repository contains secret-looking strings (local complement to gitleaks in CI)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
for p in ("packages/ml", "packages/governance", "packages/shared"):
    sys.path.insert(0, str(ROOT / p))

from modelguard_api.services.security import scan_for_secrets  # noqa: E402

result = scan_for_secrets(
    [ROOT / "apps", ROOT / "packages", ROOT / "docs", ROOT / "scripts", ROOT / "tests", ROOT / "infra"]
)
print(json.dumps(result, indent=2))
sys.exit(0 if result["status"] == "pass" else 1)

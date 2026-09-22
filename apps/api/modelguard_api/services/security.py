"""Local security evidence: a lightweight secrets scan and a raw-row leak check.

These are portfolio-grade checks that produce real evidence for the readiness engine; CI runs
gitleaks as the authoritative scan.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SECRET_PATTERNS = {
    "anthropic_key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai_key": re.compile(r"sk-[A-Za-z0-9]{32,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "generic_secret": re.compile(r"(?i)(password|secret|api_key)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
}
RAW_ROW = re.compile(r"\bln_[0-9a-f]{12}\b")
SCAN_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".toml", ".env", ".txt", ".ts", ".tsx"}
SKIP_DIRS = {".venv", "node_modules", ".git", "data", "artifacts", "__pycache__", "dist"}


def _iter_files(roots: list[Path]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root.is_file():
            out.append(root)
            continue
        for p in root.rglob("*"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.is_file() and p.suffix in SCAN_SUFFIXES and p.name != ".env.example":
                out.append(p)
    return out


def scan_for_secrets(roots: list[Path]) -> dict[str, Any]:
    findings = []
    for path in _iter_files(roots):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"file": str(path), "pattern": name})
    return {
        "status": "pass" if not findings else "fail",
        "files_scanned": len(_iter_files(roots)),
        "findings": findings,
    }


def raw_rows_present(texts: list[str]) -> bool:
    return any(RAW_ROW.search(t or "") for t in texts)

"""Versioned governance documents: types, front matter, templates and completeness checks.

Documents are Markdown with YAML front matter. A document is *complete* when its status is
'complete' and every required section heading exists with real content (no TODO placeholders).
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "docs" / "governance" / "templates"
PLACEHOLDER_RE = re.compile(r"\bTODO\b|\[TBD\]|<fill in>", re.IGNORECASE)


class DocumentType(StrEnum):
    INTENDED_USE = "intended_use"
    MODEL_CARD = "model_card"
    DATA_LINEAGE = "data_lineage"
    VALIDATION_REPORT = "validation_report"
    MONITORING_PLAN = "monitoring_plan"
    CONTROL_MATRIX = "control_matrix"
    RISK_ASSESSMENT = "risk_assessment"
    CHANGE_LOG = "change_log"


DOCUMENT_TITLES: dict[DocumentType, str] = {
    DocumentType.INTENDED_USE: "Product Requirements and Intended-Use Statement",
    DocumentType.MODEL_CARD: "Model Card",
    DocumentType.DATA_LINEAGE: "Data Lineage and Data Dictionary",
    DocumentType.VALIDATION_REPORT: "Validation Report",
    DocumentType.MONITORING_PLAN: "Monitoring Plan",
    DocumentType.CONTROL_MATRIX: "Risk-Control Matrix",
    DocumentType.RISK_ASSESSMENT: "AI/Model Risk Assessment and Readiness Checklist",
    DocumentType.CHANGE_LOG: "Change Log and Release Notes",
}

REQUIRED_SECTIONS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.INTENDED_USE: ("Business purpose", "Intended use", "Out-of-scope uses", "Users and decisions"),
    DocumentType.MODEL_CARD: (
        "Model name and version",
        "Business purpose and intended use",
        "Out-of-scope uses",
        "Data source, license, and lineage",
        "Target definition and modeling approach",
        "Feature list and excluded-feature rationale",
        "Training/validation split and reproducibility settings",
        "Performance, calibration, and fairness results",
        "Known limitations and failure modes",
        "Monitoring plan and alert thresholds",
        "Controls and owners",
        "Approval state and change log",
    ),
    DocumentType.DATA_LINEAGE: ("Source", "Lineage chain", "Data dictionary", "Quality results"),
    DocumentType.VALIDATION_REPORT: (
        "Scope",
        "Discrimination",
        "Calibration",
        "Threshold analysis",
        "Feature importance",
        "Hypothesis test",
        "Fairness diagnostics",
        "Limitations",
        "Reviewer status",
    ),
    DocumentType.MONITORING_PLAN: ("Baseline distributions", "PSI configuration", "Alert thresholds", "Owner and cadence", "Escalation"),
    DocumentType.CONTROL_MATRIX: ("Controls",),
    DocumentType.RISK_ASSESSMENT: ("Risk summary", "Fairness assessment", "Readiness checklist", "Residual risk"),
    DocumentType.CHANGE_LOG: ("Changes",),
}


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    return (meta if isinstance(meta, dict) else {}), parts[2].lstrip("\n")


def dump_document(meta: dict[str, Any], body: str) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False).strip() + "\n---\n\n" + body.lstrip("\n")


def sections(body: str) -> dict[str, str]:
    """Map '## heading' -> section text (text before the first heading is keyed '')."""
    out: dict[str, str] = {}
    current = ""
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            out[current] = "\n".join(buf).strip()
            current, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    out[current] = "\n".join(buf).strip()
    return out


def missing_sections(doc_type: DocumentType, text: str) -> list[str]:
    """Required headings that are absent, empty, or still contain a placeholder."""
    _, body = parse_front_matter(text)
    present = {k.lower(): v for k, v in sections(body).items()}
    gaps = []
    for name in REQUIRED_SECTIONS[doc_type]:
        content = present.get(name.lower())
        if content is None or not content.strip() or PLACEHOLDER_RE.search(content):
            gaps.append(name)
    return gaps


def load_template(doc_type: DocumentType) -> str:
    return (TEMPLATE_DIR / f"{doc_type.value}.md").read_text()


def render_template(doc_type: DocumentType, context: dict[str, Any]) -> str:
    """Very small `{{ key }}` substitution; unknown keys are left as TODO placeholders."""
    text = load_template(doc_type)

    def sub(m: re.Match[str]) -> str:
        key = m.group(1).strip()
        val = context.get(key)
        return "TODO" if val is None else str(val)

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", sub, text)

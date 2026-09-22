"""Copilot completeness accuracy against the hand-authored scenarios in tests/fixtures/copilot_eval.json.

The rule-based provider is scored offline on every run. Hosted providers are scored only when
their API key is present (never in CI), so the published number is for the offline provider.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from modelguard_governance.copilot.provider import AnthropicProvider, RuleBasedProvider
from modelguard_governance.copilot.service import answer_question

CASES = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "copilot_eval.json").read_text())["cases"]
DOCS = [
    {
        "id": "model-card-v1",
        "type": "model_card",
        "status": "complete",
        "content": "## Known limitations and failure modes\n\nSynthetic data.\n\n## Monitoring plan and alert thresholds\n\nPSI 0.10/0.25.",
    },
    {
        "id": "risk-assessment-v1",
        "type": "risk_assessment",
        "status": "complete",
        "content": "## Fairness assessment\n\nDiagnostics on synthetic group.\n\n## Readiness checklist\n\nSee engine.",
    },
]


def _score(provider) -> tuple[int, list[str]]:
    hits, failures = 0, []
    for case in CASES:
        r = answer_question(
            question="What evidence is missing before approval?",
            model_version="v",
            state="VALIDATED",
            documents=DOCS,
            readiness=case["readiness"],
            provider=provider,
        )
        got = sorted(m.requirement for m in r.response.missing_requirements if m.status != "present")
        if got == sorted(case["expected_missing"]):
            hits += 1
        else:
            failures.append(f"{case['name']}: expected {case['expected_missing']} got {got}")
    return hits, failures


def test_rule_based_completeness_accuracy(capsys):
    hits, failures = _score(RuleBasedProvider())
    print(f"\ncopilot completeness accuracy (rule_based): {hits}/{len(CASES)} = {hits / len(CASES):.0%}")
    assert not failures, failures
    assert hits == len(CASES)


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="hosted provider eval needs ANTHROPIC_API_KEY")
def test_anthropic_completeness_accuracy():  # pragma: no cover - network
    hits, failures = _score(AnthropicProvider())
    print(f"\ncopilot completeness accuracy (anthropic): {hits}/{len(CASES)}")
    assert hits >= len(CASES) - 1, failures

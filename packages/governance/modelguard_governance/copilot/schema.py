"""Structured copilot response contract, validated with Pydantic before anything is returned."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DISCLAIMER = "Portfolio governance assistant; not an approval authority."


class MissingRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requirement: str = Field(min_length=1, max_length=200)
    status: Literal["missing", "incomplete", "present"]
    evidence: list[str] = Field(default_factory=list, max_length=50)


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(min_length=1, max_length=200)
    section: str = Field(min_length=1, max_length=200)


class CopilotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1, max_length=4000)
    missing_requirements: list[MissingRequirement] = Field(default_factory=list, max_length=50)
    citations: list[Citation] = Field(default_factory=list, max_length=50)
    confidence: Literal["high", "medium", "low"]
    disclaimer: str = DISCLAIMER


def safe_fallback(reason: str) -> CopilotResponse:
    return CopilotResponse(
        answer=(
            "The copilot could not produce a validated answer for this request "
            f"({reason}). Review the readiness checklist directly."
        ),
        missing_requirements=[],
        citations=[],
        confidence="low",
        disclaimer=DISCLAIMER,
    )

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DataSourceIn(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]{3,64}$")
    name: str
    license_url: str
    license_name: str = ""
    retrieval_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    intended_use: str
    limitations: str


class DataSourceOut(ORM):
    id: str
    name: str
    license_url: str
    license_name: str
    retrieval_date: str
    intended_use: str
    limitations: str
    doc_path: str
    license_confirmed_by: str | None
    created_at: datetime


class SnapshotImportIn(BaseModel):
    source_id: str
    file_path: str
    as_of_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    purpose: Literal["training", "monitoring"] = "training"


class SnapshotOut(ORM):
    id: str
    source_id: str
    file_path: str
    as_of_date: str
    row_count: int
    checksum: str
    schema_hash: str
    quality_status: str
    quality_json: dict[str, Any]
    profile_json: dict[str, Any]
    purpose: str
    created_at: datetime


class TrainingRunIn(BaseModel):
    snapshot_id: str
    random_seed: int = 42
    hyperparameters: dict[str, dict[str, Any]] | None = None


class TrainingRunOut(ORM):
    id: str
    snapshot_id: str
    git_sha: str | None
    random_seed: int
    config_json: dict[str, Any]
    status: str
    error: str | None
    artifacts_json: dict[str, Any]
    metrics_json: dict[str, Any]
    hypothesis_tests_json: list[Any]
    requested_by: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ModelVersionIn(BaseModel):
    training_run_id: str
    semantic_version: str
    model_type: Literal["baseline", "champion"] = "champion"
    description: str = ""


class ModelVersionOut(ORM):
    id: str
    semantic_version: str
    training_run_id: str
    state: str
    artifact_uri: str
    model_type: str
    owner: str
    description: str
    retirement_reason: str | None
    created_at: datetime
    updated_at: datetime


class MetricOut(ORM):
    scope: str
    metric_name: str
    metric_value: float
    lower_ci: float | None
    upper_ci: float | None
    batch_id: str | None


class DocumentOut(ORM):
    id: str
    type: str
    version: int
    content_hash: str
    status: str
    path: str
    updated_at: datetime


class DocumentDetailOut(DocumentOut):
    content: str


class ControlIn(BaseModel):
    control_name: str
    description: str = ""
    owner: str
    frequency: str
    status: str
    evidence_uri: str = ""
    test_evidence: str = ""


class ControlOut(ORM, ControlIn):
    id: str


class ReadinessOut(BaseModel):
    check_name: str
    status: str
    missing: list[str]
    evidence: dict[str, Any]


class DecisionIn(BaseModel):
    decision: Literal["approve", "reject"]
    rationale: str = Field(min_length=3)


class RetireIn(BaseModel):
    reason: str = Field(min_length=3)


class NarrativeIn(BaseModel):
    narrative: dict[str, str]


class DocumentStatusIn(BaseModel):
    status: Literal["draft", "complete"]


class ApprovalOut(ORM):
    id: str
    reviewer_id: str
    decision: str
    rationale: str
    decided_at: datetime


class AlertOut(ORM):
    id: str
    monitoring_batch_id: str
    type: str
    severity: str
    status: str
    title: str
    detail_json: dict[str, Any]
    owner: str
    due_date: str
    investigation_note: str | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime


class AlertUpdateIn(BaseModel):
    status: Literal["open", "investigating", "resolved"]
    note: str = ""


class MonitoringBatchIn(BaseModel):
    snapshot_id: str


class MonitoringBatchOut(ORM):
    id: str
    snapshot_id: str
    as_of_date: str
    status: str
    labels_available: bool
    results_json: dict[str, Any]
    created_at: datetime


class AuditEventOut(BaseModel):
    id: int
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    before_json: Any
    after_json: Any
    occurred_at: str
    previous_hash: str
    event_hash: str


class ModelVersionDetailOut(ModelVersionOut):
    training_run: TrainingRunOut
    snapshot: SnapshotOut
    source: DataSourceOut
    metrics: list[MetricOut]
    artifacts: dict[str, Any]
    documents: list[DocumentOut]
    controls: list[ControlOut]
    readiness: list[ReadinessOut]
    decisions: list[ApprovalOut]
    alerts: list[AlertOut]
    audit_events: list[AuditEventOut]
    narrative: dict[str, Any]


class CopilotQueryIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    provider: str | None = None


class CopilotQueryOut(BaseModel):
    response: dict[str, Any]
    provider: str
    latency_ms: int
    cited_document_ids: list[str]
    status: str


class UserOut(ORM):
    id: str
    username: str
    role: str
    display_name: str

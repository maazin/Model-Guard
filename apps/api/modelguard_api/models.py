"""SQLAlchemy 2 models. Column types are kept portable between PostgreSQL 16 and SQLite."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from modelguard_api.db import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[str] = mapped_column(String(32))
    display_name: Mapped[str] = mapped_column(String(128))


class DataSource(Base):
    __tablename__ = "data_sources"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    license_url: Mapped[str] = mapped_column(String(500))
    license_name: Mapped[str] = mapped_column(String(200), default="")
    retrieval_date: Mapped[str] = mapped_column(String(10))
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intended_use: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str] = mapped_column(Text)
    doc_path: Mapped[str] = mapped_column(String(500))
    license_confirmed_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"))
    file_path: Mapped[str] = mapped_column(String(500))
    as_of_date: Mapped[str] = mapped_column(String(10))
    row_count: Mapped[int] = mapped_column(Integer)
    checksum: Mapped[str] = mapped_column(String(64))
    schema_hash: Mapped[str] = mapped_column(String(64))
    quality_status: Mapped[str] = mapped_column(String(16))
    quality_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    purpose: Mapped[str] = mapped_column(String(32), default="training")  # training | monitoring
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    source: Mapped[DataSource] = relationship()


class TrainingRun(Base):
    __tablename__ = "training_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("data_snapshots.id"))
    git_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    random_seed: Mapped[int] = mapped_column(Integer)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="QUEUED")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_dir: Mapped[str | None] = mapped_column(String(500), nullable=True)
    artifacts_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    hypothesis_tests_json: Mapped[list[Any]] = mapped_column(JSON, default=list)
    baseline_distributions_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    requested_by: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    snapshot: Mapped[DataSnapshot] = relationship()


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    semantic_version: Mapped[str] = mapped_column(String(64), unique=True)
    training_run_id: Mapped[str] = mapped_column(ForeignKey("training_runs.id"))
    state: Mapped[str] = mapped_column(String(32), default="DRAFT")
    artifact_uri: Mapped[str] = mapped_column(String(500))
    model_type: Mapped[str] = mapped_column(String(32))  # baseline | champion
    owner: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
    retirement_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    measured_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # filled by validation
    narrative_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)  # human-authored sections
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    training_run: Mapped[TrainingRun] = relationship()


class MetricResult(Base):
    __tablename__ = "metric_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    scope: Mapped[str] = mapped_column(String(32))  # holdout | holdout_baseline | monitoring
    metric_name: Mapped[str] = mapped_column(String(64))
    metric_value: Mapped[float] = mapped_column(Float)
    lower_ci: Mapped[float | None] = mapped_column(Float, nullable=True)
    upper_ci: Mapped[float | None] = mapped_column(Float, nullable=True)
    batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ValidationArtifact(Base):
    """Non-scalar validation outputs (curves, tables, tests) attached to a version."""

    __tablename__ = "validation_artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    payload_json: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("model_version_id", "name", name="uq_artifact_version_name"),)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer, default=1)
    content_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft | complete
    path: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("model_version_id", "type", name="uq_document_version_type"),)


class ReadinessCheck(Base):
    __tablename__ = "readiness_checks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    check_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    missing_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Control(Base):
    __tablename__ = "controls"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    control_name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str] = mapped_column(String(64))
    frequency: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32))
    evidence_uri: Mapped[str] = mapped_column(String(500), default="")
    test_evidence: Mapped[str] = mapped_column(Text, default="")


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(16))  # approve | reject
    rationale: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MonitoringBatch(Base):
    __tablename__ = "monitoring_batches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("data_snapshots.id"))
    as_of_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(16))  # ok | investigate | alert | failed
    labels_available: Mapped[bool] = mapped_column(Boolean, default=False)
    results_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    snapshot: Mapped[DataSnapshot] = relationship()


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    monitoring_batch_id: Mapped[str] = mapped_column(ForeignKey("monitoring_batches.id"), index=True)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))  # data_quality | psi | score_drift | performance | fairness
    severity: Mapped[str] = mapped_column(String(16))  # low | medium | high
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | investigating | resolved
    title: Mapped[str] = mapped_column(String(200))
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    owner: Mapped[str] = mapped_column(String(64))
    due_date: Mapped[str] = mapped_column(String(10))
    investigation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    before_json: Mapped[Any] = mapped_column(JSON, nullable=True)
    after_json: Mapped[Any] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[str] = mapped_column(String(32))
    previous_hash: Mapped[str] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64), unique=True)


class CopilotQuery(Base):
    __tablename__ = "copilot_queries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32))
    cited_document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16))
    latency_ms: Mapped[int] = mapped_column(Integer)
    question_length: Mapped[int] = mapped_column(Integer, default=0)  # metadata only; never the text
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

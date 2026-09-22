from __future__ import annotations

import subprocess
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from modelguard_ml.training import save_artifacts, train_models
from modelguard_shared.jsonutil import sanitize
from sqlalchemy.orm import Session

from modelguard_api.config import ROOT, get_settings
from modelguard_api.db import SessionLocal
from modelguard_api.errors import bad_request, not_found
from modelguard_api.models import DataSnapshot, TrainingRun, User
from modelguard_api.services.audit import record_event
from modelguard_api.services.lineage import load_frame


def git_sha() -> str | None:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5, check=False
            ).stdout.strip()
            or None
        )
    except (OSError, subprocess.SubprocessError):
        return None


def create_run(
    db: Session, *, snapshot_id: str, seed: int, hyperparams: dict[str, Any] | None, user: User
) -> TrainingRun:
    snap = db.get(DataSnapshot, snapshot_id)
    if snap is None:
        raise not_found("snapshot", snapshot_id)
    if snap.quality_status == "fail":
        raise bad_request("snapshot failed data-quality checks; fix the data before training")
    if snap.purpose != "training":
        raise bad_request("snapshot was imported for monitoring, not training")
    run = TrainingRun(
        snapshot_id=snapshot_id,
        random_seed=seed,
        git_sha=git_sha(),
        config_json={"hyperparameters": hyperparams or {}},
        requested_by=user.username,
        status="QUEUED",
    )
    db.add(run)
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action="training_run.queued",
        entity_type="training_run",
        entity_id=run.id,
        after={"snapshot_id": snapshot_id, "seed": seed},
    )
    db.commit()
    return run


def execute_run(run_id: str) -> None:
    """Runs in a background task with its own session; status is persisted at each step."""
    settings = get_settings()
    db = SessionLocal()
    try:
        run = db.get(TrainingRun, run_id)
        if run is None:
            return
        run.status = "RUNNING"
        run.started_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        snap = db.get(DataSnapshot, run.snapshot_id)
        assert snap is not None
        df = load_frame(ROOT / snap.file_path)
        result = train_models(
            df,
            seed=run.random_seed,
            data_checksum=snap.checksum,
            hyperparams=run.config_json.get("hyperparameters") or None,
            n_bootstrap=settings.n_bootstrap,
            git_sha=run.git_sha,
        )
        out_dir = Path(settings.artifact_dir) / "runs" / run.id
        paths = save_artifacts(result, out_dir)
        run.artifact_dir = str(out_dir)
        run.artifacts_json = paths
        run.config_json = sanitize(result.config)
        run.metrics_json = sanitize({k: v.to_dict() for k, v in result.evaluations.items()})
        run.hypothesis_tests_json = sanitize(result.hypothesis_tests)
        run.baseline_distributions_json = sanitize(result.baseline_distributions)
        run.status = "COMPLETED"
        run.completed_at = datetime.now(UTC).replace(tzinfo=None)
        record_event(
            db,
            actor_id=run.requested_by,
            action="training_run.completed",
            entity_type="training_run",
            entity_id=run.id,
            after={"metrics": {k: v["metrics"] for k, v in run.metrics_json.items()}, "seed": run.random_seed},
        )
        db.commit()
    except Exception:  # noqa: BLE001 - persist failure state
        db.rollback()
        run = db.get(TrainingRun, run_id)
        if run is not None:
            run.status = "FAILED"
            run.error = traceback.format_exc()[-4000:]
            run.completed_at = datetime.now(UTC).replace(tzinfo=None)
            db.commit()
    finally:
        db.close()

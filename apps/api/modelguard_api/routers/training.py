from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api import schemas
from modelguard_api.auth import current_user, require_role
from modelguard_api.db import get_db
from modelguard_api.errors import not_found
from modelguard_api.models import TrainingRun, User
from modelguard_api.services import training

router = APIRouter(prefix="/api/v1/training-runs", tags=["training"])


@router.post("", response_model=schemas.TrainingRunOut, status_code=202)
def start_run(
    payload: schemas.TrainingRunIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("data_scientist")),
):
    run = training.create_run(
        db, snapshot_id=payload.snapshot_id, seed=payload.random_seed, hyperparams=payload.hyperparameters, user=user
    )
    background.add_task(training.execute_run, run.id)
    return run


@router.get("", response_model=list[schemas.TrainingRunOut])
def list_runs(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return list(db.scalars(select(TrainingRun).order_by(TrainingRun.created_at)))


@router.get("/{run_id}", response_model=schemas.TrainingRunOut)
def get_run(run_id: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    run = db.get(TrainingRun, run_id)
    if run is None:
        raise not_found("training run", run_id)
    return run

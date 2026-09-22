"""Monitoring batches: data quality, PSI, score drift, labelled performance, alerts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
from modelguard_governance.documents import DocumentType, parse_front_matter
from modelguard_governance.lifecycle import Action, State
from modelguard_ml import metrics as M
from modelguard_ml.data_quality import run_quality_checks
from modelguard_ml.drift import categorical_psi, open_edges, psi_from_distributions, psi_status
from modelguard_ml.fairness import group_metrics
from modelguard_ml.stats_tests import two_sample_ks
from modelguard_ml.training import load_pipeline
from modelguard_shared.constants import (
    CATEGORICAL_FEATURES,
    MODEL_FEATURES,
    NUMERIC_FEATURES,
    PSI_ALERT,
    PSI_INVESTIGATE,
)
from modelguard_shared.jsonutil import sanitize
from sqlalchemy import select
from sqlalchemy.orm import Session

from modelguard_api.config import ROOT
from modelguard_api.errors import bad_request, conflict, not_found
from modelguard_api.models import Alert, DataSnapshot, MetricResult, ModelVersion, MonitoringBatch, User
from modelguard_api.services import documents as docsvc
from modelguard_api.services.audit import record_event
from modelguard_api.services.lineage import load_frame

SEVERITY_DUE_DAYS = {"high": 7, "medium": 14, "low": 30}


def thresholds_for(db: Session, mv: ModelVersion) -> dict[str, float]:
    doc = next((d for d in docsvc.get_documents(db, mv) if d.type == DocumentType.MONITORING_PLAN.value), None)
    meta = parse_front_matter(doc.content)[0] if doc else {}
    t = meta.get("alert_thresholds") or {}
    return {
        "psi_investigate": float(t.get("psi_investigate", PSI_INVESTIGATE)),
        "psi_alert": float(t.get("psi_alert", PSI_ALERT)),
        "auc_drop": float(t.get("auc_drop", docsvc.DEFAULT_AUC_DROP)),
        "null_rate_max": float(t.get("null_rate_max", 0.05)),
        "duplicate_rate_max": float(t.get("duplicate_rate_max", 0.01)),
    }


def _alert(
    batch: MonitoringBatch, mv: ModelVersion, type_: str, severity: str, title: str, detail: dict[str, Any]
) -> Alert:
    due = (date.today() + timedelta(days=SEVERITY_DUE_DAYS[severity])).isoformat()
    return Alert(
        monitoring_batch_id=batch.id,
        model_version_id=mv.id,
        type=type_,
        severity=severity,
        status="open",
        title=title,
        detail_json=detail,
        owner=mv.owner,
        due_date=due,
    )


def run_batch(db: Session, mv: ModelVersion, *, snapshot_id: str, user: User) -> MonitoringBatch:
    if mv.state not in (State.APPROVED, State.MONITORING):
        raise conflict(f"monitoring requires an APPROVED or MONITORING model; {mv.semantic_version} is {mv.state}")
    snap = db.get(DataSnapshot, snapshot_id)
    if snap is None:
        raise not_found("snapshot", snapshot_id)
    if db.scalar(
        select(MonitoringBatch).where(
            MonitoringBatch.model_version_id == mv.id, MonitoringBatch.snapshot_id == snapshot_id
        )
    ):
        raise bad_request("this snapshot has already been evaluated for this model version")
    th = thresholds_for(db, mv)
    run = mv.training_run
    baseline = run.baseline_distributions_json
    df = load_frame(ROOT / snap.file_path)
    quality = run_quality_checks(
        df, require_target=False, max_null_rate=th["null_rate_max"], max_duplicate_rate=th["duplicate_rate_max"]
    )
    batch = MonitoringBatch(
        model_version_id=mv.id,
        snapshot_id=snap.id,
        as_of_date=snap.as_of_date,
        status="ok",
        labels_available=bool(quality.target_available),
    )
    db.add(batch)
    db.flush()
    alerts: list[Alert] = []
    results: dict[str, Any] = {
        "thresholds": th,
        "data_quality": quality.to_dict(),
        "psi": {},
        "labels_available": quality.target_available,
    }

    for issue in quality.issues:
        if issue.severity == "error":
            alerts.append(
                _alert(
                    batch,
                    mv,
                    "data_quality",
                    "high",
                    f"Data quality: {issue.check} ({issue.field or 'batch'})",
                    {"detail": issue.detail},
                )
            )
    if quality.status == "fail":
        batch.status = "failed"
        batch.results_json = sanitize(results)
        db.add_all(alerts)
        _finish(db, mv, batch, alerts, user)
        return batch

    # PSI per feature against stored training distributions.
    for col in NUMERIC_FEATURES:
        ref = baseline["numeric"][col]
        edges = np.array(ref["edges"], dtype=float)
        cur = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
        cur = cur[~np.isnan(cur)]
        counts, _ = np.histogram(cur, bins=open_edges(edges))
        value = psi_from_distributions(np.array(ref["expected_pct"]), counts)
        results["psi"][col] = {
            "psi": value,
            "status": psi_status(value, th["psi_investigate"], th["psi_alert"]),
            "expected_pct": ref["expected_pct"],
            "actual_pct": (counts / max(counts.sum(), 1)).round(6).tolist(),
            "bins": ref["edges"],
        }
    for col in CATEGORICAL_FEATURES + ("region",):
        if col in baseline.get("categorical", {}) and col in df.columns:
            ref = baseline["categorical"][col]
            base_series = pd.Series(list(ref.keys())).repeat([int(round(v * 10000)) for v in ref.values()])
            r = categorical_psi(base_series, df[col].astype(str))
            r["status"] = psi_status(r["psi"], th["psi_investigate"], th["psi_alert"])
            results["psi"][col] = r
    for col, r in results["psi"].items():
        if r["status"] == "alert":
            alerts.append(
                _alert(
                    batch,
                    mv,
                    "psi",
                    "high",
                    f"PSI alert on {col} ({r['psi']:.3f})",
                    {"feature": col, "psi": r["psi"], "threshold": th["psi_alert"]},
                )
            )
        elif r["status"] == "investigate":
            alerts.append(
                _alert(
                    batch,
                    mv,
                    "psi",
                    "medium",
                    f"PSI investigate on {col} ({r['psi']:.3f})",
                    {"feature": col, "psi": r["psi"], "threshold": th["psi_investigate"]},
                )
            )

    # Score drift.
    pipe = load_pipeline(mv.artifact_uri)
    scores = pipe.predict_proba(df[list(MODEL_FEATURES)])[:, 1]
    ref_scores = baseline["scores"]
    counts, _ = np.histogram(scores, bins=open_edges(np.array(ref_scores["edges"])))
    sd = {
        "psi": psi_from_distributions(np.array(ref_scores["expected_pct"]), counts),
        "baseline_mean": ref_scores["mean"],
        "current_mean": float(scores.mean()),
        "mean_shift": float(scores.mean() - ref_scores["mean"]),
        "actual_pct": (counts / max(counts.sum(), 1)).round(6).tolist(),
        "expected_pct": ref_scores["expected_pct"],
    }
    sd["status"] = psi_status(sd["psi"], th["psi_investigate"], th["psi_alert"])
    results["score_drift"] = sd
    if sd["status"] == "alert":
        alerts.append(
            _alert(
                batch,
                mv,
                "score_drift",
                "high",
                f"Prediction score drift (PSI {sd['psi']:.3f})",
                {"psi": sd["psi"], "mean_shift": sd["mean_shift"]},
            )
        )
    elif sd["status"] == "investigate":
        alerts.append(
            _alert(
                batch,
                mv,
                "score_drift",
                "medium",
                f"Prediction score shift to investigate (PSI {sd['psi']:.3f})",
                {"psi": sd["psi"], "mean_shift": sd["mean_shift"]},
            )
        )

    # Hypothesis test on the most drifted numeric feature.
    worst = max(NUMERIC_FEATURES, key=lambda c: results["psi"][c]["psi"])
    train_df = load_frame(ROOT / run.snapshot.file_path)
    results["hypothesis_test"] = two_sample_ks(
        train_df[worst].to_numpy(dtype=float), pd.to_numeric(df[worst], errors="coerce").to_numpy(dtype=float), worst
    )

    # Labelled performance.
    holdout_auc = run.metrics_json[mv.model_type]["metrics"]["auc"]["value"]
    if quality.target_available:
        y = pd.to_numeric(df["default_flag"], errors="coerce").to_numpy(dtype=float)
        mask = ~np.isnan(y)
        y, p = y[mask], scores[mask]
        auc_ci = M.bootstrap_ci(y, p, M.auc_roc, n_bootstrap=200, seed=run.random_seed)
        cal = M.calibration(y, p)
        perf = {
            "auc": {"value": auc_ci.point, "lower_ci": auc_ci.lower, "upper_ci": auc_ci.upper},
            "ks": {"value": M.ks_statistic(y, p)},
            "brier": {"value": M.brier_score(y, p)},
            "ece": {"value": cal.ece},
            "observed_default_rate": {"value": float(y.mean())},
            "mean_predicted": {"value": float(p.mean())},
            "n": {"value": float(len(y))},
        }
        results["performance"] = perf
        results["calibration"] = cal.to_dict()
        results["holdout_auc"] = holdout_auc
        for name, v in perf.items():
            db.add(
                MetricResult(
                    model_version_id=mv.id,
                    scope="monitoring",
                    metric_name=name,
                    metric_value=v["value"],
                    lower_ci=v.get("lower_ci"),
                    upper_ci=v.get("upper_ci"),
                    batch_id=batch.id,
                )
            )
        drop = holdout_auc - auc_ci.point
        if drop > th["auc_drop"]:
            alerts.append(
                _alert(
                    batch,
                    mv,
                    "performance",
                    "high",
                    f"AUC dropped {drop:.3f} below holdout",
                    {"holdout_auc": holdout_auc, "batch_auc": auc_ci.point, "threshold": th["auc_drop"]},
                )
            )
        if abs(perf["observed_default_rate"]["value"] - perf["mean_predicted"]["value"]) > 0.05:
            alerts.append(
                _alert(
                    batch,
                    mv,
                    "performance",
                    "medium",
                    "Calibration gap: observed vs predicted default rate differs by > 5pp",
                    {"observed": perf["observed_default_rate"]["value"], "predicted": perf["mean_predicted"]["value"]},
                )
            )
        if "fairness_group" in df.columns:
            fair = group_metrics(
                y, p, df["fairness_group"].to_numpy()[mask], run.config_json.get("illustrative_threshold", 0.5)
            )
            results["fairness"] = fair
            if fair["selection_rate_ratio"] < 0.8:
                alerts.append(
                    _alert(
                        batch,
                        mv,
                        "fairness",
                        "medium",
                        f"Selection-rate ratio {fair['selection_rate_ratio']:.2f} below 0.80 diagnostic",
                        {"ratio": fair["selection_rate_ratio"]},
                    )
                )

    sev = {a.severity for a in alerts}
    batch.status = "alert" if "high" in sev else ("investigate" if sev else "ok")
    batch.results_json = sanitize(results)
    db.add_all(alerts)
    _finish(db, mv, batch, alerts, user)
    return batch


def _finish(db: Session, mv: ModelVersion, batch: MonitoringBatch, alerts: list[Alert], user: User) -> None:
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action="monitoring_batch.evaluated",
        entity_type="monitoring_batch",
        entity_id=batch.id,
        after={
            "model_version_id": mv.id,
            "as_of_date": batch.as_of_date,
            "status": batch.status,
            "alerts": [a.title for a in alerts],
        },
    )
    for a in alerts:
        record_event(
            db,
            actor_id=user.username,
            action="alert.created",
            entity_type="alert",
            entity_id=a.id,
            after={"type": a.type, "severity": a.severity, "title": a.title, "owner": a.owner, "due_date": a.due_date},
        )
    if mv.state == State.APPROVED:
        from modelguard_api.services.registry import _transition

        _transition(db, mv, Action.START_MONITORING, user, {"first_batch_id": batch.id})
    db.commit()


def update_alert(db: Session, alert: Alert, *, status: str, note: str, user: User) -> Alert:
    if status not in ("open", "investigating", "resolved"):
        raise bad_request("status must be open, investigating or resolved")
    if status == "resolved" and not note.strip():
        raise bad_request("a resolution note is required to resolve an alert")
    before = {
        "status": alert.status,
        "investigation_note": alert.investigation_note,
        "resolution_note": alert.resolution_note,
    }
    alert.status = status
    if status == "investigating":
        alert.investigation_note = note
    if status == "resolved":
        alert.resolution_note = note
    db.flush()
    record_event(
        db,
        actor_id=user.username,
        action=f"alert.{status}",
        entity_type="alert",
        entity_id=alert.id,
        before=before,
        after={"status": status, "note": note},
    )
    db.commit()
    return alert


def batches_for(db: Session, mv: ModelVersion) -> list[MonitoringBatch]:
    return list(
        db.scalars(
            select(MonitoringBatch)
            .where(MonitoringBatch.model_version_id == mv.id)
            .order_by(MonitoringBatch.as_of_date)
        )
    )


def alerts_for(db: Session, mv: ModelVersion) -> list[Alert]:
    return list(db.scalars(select(Alert).where(Alert.model_version_id == mv.id).order_by(Alert.created_at)))

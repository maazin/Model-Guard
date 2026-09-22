"""Seed the demo: users, licensed-fixture source, snapshots, three model versions.

- pd-credit-v1.0.0  champion, APPROVED -> MONITORING with three quarterly batches (drift alerts)
- pd-credit-v1.1.0  champion candidate, complete package, PENDING_REVIEW (reviewer decides in UI)
- pd-credit-v1.2.0  candidate with an incomplete package; submit-review is blocked by the gate

Everything goes through the same service functions the API uses, so the seeded state is
exactly what a user could reproduce by hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for p in ("apps/api", "packages/ml", "packages/governance", "packages/shared"):
    sys.path.insert(0, str(ROOT / p))

from modelguard_shared.constants import DEMO_USERS  # noqa: E402

UCI_RAW = ROOT / "data" / "sources" / "uci-credit-default-2005" / "default of credit card clients.xls"
UCI_SOURCE = {
    "id": "uci-credit-default-2005",
    "name": "UCI 350 - Default of Credit Card Clients (Yeh & Lien, 2009)",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "license_name": "CC BY 4.0 (UCI ML Repository listing, confirmed 2026-09-22)",
    "retrieval_date": "2026-09-22",
    "intended_use": (
        "Sharing and adaptation for any purpose with attribution. Citation: Yeh, I. (2009). Default of Credit Card "
        "Clients [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H. Used here for a "
        "portfolio PD-model lifecycle simulation."
    ),
    "limitations": (
        "Single September-2005 cross-section of Taiwanese credit-card holders: no time axis (stratified split), "
        "card revolving balances rather than instalment loans, NT$ amounts, and demographic fields that are "
        "excluded from features. Monitoring batches are generated samples with induced shift, not later cohorts."
    ),
}
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from modelguard_api.db import Base, SessionLocal, engine  # noqa: E402
from modelguard_api.errors import Problem  # noqa: E402
from modelguard_api.models import Alert, User  # noqa: E402
from modelguard_api.services import lineage, monitoring, registry, training  # noqa: E402

SOURCE = {
    "id": "synthetic-loans-v1",
    "name": "ModelGuard synthetic loan-performance fixture",
    "license_url": "https://opensource.org/license/mit",
    "license_name": "MIT (generated in-repo; no real borrowers)",
    "retrieval_date": "2026-09-22",
    "intended_use": "Offline development, tests and the local demo of the ModelGuard lifecycle. Not derived from real consumers.",
    "limitations": "Parametric synthetic process; relationships are simpler than real credit data and the default rate is stylised.",
}

NARRATIVE = {
    "business_purpose": (
        "Estimate the probability that a consumer instalment loan defaults within the observation window so that "
        "portfolio risk can be ranked and monitored. Portfolio simulation only; not used for any real lending decision."
    ),
    "intended_use": "Rank-ordering and monitoring of PD on the synthetic/licensed loan-performance dataset inside ModelGuard.",
    "out_of_scope": "Credit decisions, pricing, collections prioritisation, any real borrower, and any regulatory reporting.",
    "users_and_decisions": "Data scientist (develops), model risk reviewer (approves/rejects), risk leader (reads the executive summary). No automated decision is taken.",
    "target_definition": (
        "`default_flag` = 1 when the synthetic borrower defaults within the observation window. Leakage controls: no post-outcome "
        "fields exist in the schema; `as_of_date` is used only for the temporal split; identifiers and geography are excluded (ADR-0004)."
    ),
    "monitoring_owner": "data_scientist",
    "cadence_text": "quarterly batches, or ad hoc after a data-quality incident.",
    "escalation": "PSI alert or AUC drop beyond threshold -> open alert to the owner within 7 days -> reviewer informed -> retrain or retire decision recorded in the audit log.",
    "risk_summary": (
        "Moderate model risk for a portfolio simulation: tabular supervised model with explainable features, temporal holdout, "
        "human approval gate, and quarterly drift monitoring. Key risks are population shift and over-interpretation of the illustrative threshold."
    ),
    "fairness_assessment": (
        "Diagnostics computed on the synthetic `fairness_group` field (selection-rate ratio, TPR/FPR differences, group calibration). "
        "The field is never a model feature. Results are informational and not a legal determination."
    ),
    "residual_risk": "Accepted for portfolio demonstration use only; any real deployment would require a licensed dataset, legal review and an independent validation.",
}

CONTROLS = [
    {
        "control_name": "Data quality gate",
        "description": "Schema, range, null and duplicate checks block training on failed snapshots.",
        "owner": "data_scientist",
        "frequency": "per snapshot",
        "status": "tested",
        "evidence_uri": "tests/unit/test_data_quality.py",
        "test_evidence": "8 unit tests",
    },
    {
        "control_name": "Reproducible training",
        "description": "Seed, hyperparameters, package versions and data checksum stored with every run.",
        "owner": "data_scientist",
        "frequency": "per run",
        "status": "tested",
        "evidence_uri": "tests/unit/test_training.py",
        "test_evidence": "deterministic metrics test",
    },
    {
        "control_name": "Human approval gate",
        "description": "Only the reviewer role can approve; readiness engine must pass first.",
        "owner": "reviewer",
        "frequency": "per version",
        "status": "tested",
        "evidence_uri": "tests/integration/test_lifecycle_api.py",
        "test_evidence": "role enforcement tests",
    },
    {
        "control_name": "Monitoring and alerting",
        "description": "PSI, score drift, data quality and performance alerts with owner and due date.",
        "owner": "data_scientist",
        "frequency": "quarterly",
        "status": "implemented",
        "evidence_uri": "apps/api/modelguard_api/services/monitoring.py",
        "test_evidence": "drift alert integration test",
    },
    {
        "control_name": "Hash-chained audit log",
        "description": "Append-only events with SHA-256 chain; tampering is detectable via /audit-events/verify.",
        "owner": "reviewer",
        "frequency": "continuous",
        "status": "tested",
        "evidence_uri": "tests/unit/test_audit_chain.py",
        "test_evidence": "tamper detection tests",
    },
    {
        "control_name": "Copilot data boundary",
        "description": "Retrieval limited to governance documents; raw rows and secrets never reach a prompt.",
        "owner": "data_scientist",
        "frequency": "continuous",
        "status": "tested",
        "evidence_uri": "tests/unit/test_copilot.py",
        "test_evidence": "prompt-injection and raw-row tests",
    },
]


UCI_NARRATIVE = {
    **NARRATIVE,
    "business_purpose": (
        "Estimate the probability that a credit-card holder defaults on next month's payment from six months of "
        "billing and repayment history, so that portfolio risk can be ranked and monitored. Portfolio simulation on "
        "the public UCI 350 dataset; not used for any real lending decision."
    ),
    "intended_use": "Rank-ordering and monitoring of next-month default probability on the UCI 350 credit-card dataset.",
    "target_definition": (
        "`default_flag` = UCI variable `default payment next month` (October 2005). Leakage controls: only April to "
        "September 2005 billing/payment history is used; identifiers and demographic fields (sex, age, education, "
        "marriage) are excluded from features (ADR-0004); `sex` is retained solely for fairness diagnostics."
    ),
    "fairness_assessment": (
        "Diagnostics computed on the dataset's `sex` field (selection-rate ratio, TPR/FPR differences, group "
        "calibration). The field is never a model feature. Results are informational and not a legal determination."
    ),
    "changes": "- First version trained on a licensed public dataset (UCI 350, CC BY 4.0) with a stratified split.",
}


def seed_users(db: Session) -> dict[str, User]:
    users = {}
    for username, role in DEMO_USERS.items():
        u = db.scalar(select(User).where(User.username == username))
        if u is None:
            u = User(username=username, role=role, display_name=username.replace("_", " ").title())
            db.add(u)
        users[username] = u
    db.commit()
    return users


def seed(reset: bool = True, quiet: bool = False) -> dict[str, str]:
    log = (lambda *_: None) if quiet else print
    if reset:
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    else:
        Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        users = seed_users(db)
        ds, rev = users["data_scientist"], users["reviewer"]
        log("registering data source")
        lineage.register_source(db, SOURCE, ds)
        snap = lineage.import_snapshot(
            db,
            source_id=SOURCE["id"],
            file_path="data/fixtures/synthetic_loans.csv",
            as_of_date="2023-12-31",
            purpose="training",
            user=ds,
        )
        mon_snaps = [
            lineage.import_snapshot(
                db,
                source_id=SOURCE["id"],
                file_path=f"data/fixtures/monitoring/batch_{d}.csv",
                as_of_date=d,
                purpose="monitoring",
                user=ds,
            )
            for d in ("2024-03-31", "2024-06-30", "2024-09-30")
        ]
        log("training run A (seed 42)")
        run_a = training.create_run(db, snapshot_id=snap.id, seed=42, hyperparams=None, user=ds)
        training.execute_run(run_a.id)
        db.expire_all()
        log("training run B (seed 7, more regularised champion)")
        run_b = training.create_run(
            db, snapshot_id=snap.id, seed=7, hyperparams={"champion": {"learning_rate": 0.03, "max_iter": 200}}, user=ds
        )
        training.execute_run(run_b.id)
        db.expire_all()

        # v1.0.0 - full package, approved, monitored.
        log("v1.0.0: register, validate, document, controls, submit, approve, monitor")
        v100 = registry.register_version(
            db,
            training_run_id=run_a.id,
            semantic_version="pd-credit-v1.0.0",
            model_type="champion",
            description="Initial champion PD model.",
            user=ds,
        )
        registry.validate_version(db, v100, ds)
        registry.set_narrative(db, v100, NARRATIVE, ds)
        registry.replace_controls(db, v100, CONTROLS, ds)
        registry.submit_review(db, v100, ds)
        registry.decide(
            db,
            v100,
            "approve",
            "Package complete: lineage, validation with CIs, monitoring plan, controls and fairness diagnostics reviewed. Approved for simulated monitoring.",
            rev,
        )
        batches = [monitoring.run_batch(db, v100, snapshot_id=s.id, user=ds) for s in mon_snaps]
        alerts = monitoring.alerts_for(db, v100)
        q2 = [a for a in alerts if a.monitoring_batch_id == batches[1].id]
        if q2:
            monitoring.update_alert(
                db,
                q2[0],
                status="investigating",
                note="Mild income decline consistent with the Q2 macro narrative; watching Q3.",
                user=ds,
            )
            monitoring.update_alert(
                db,
                q2[0],
                status="resolved",
                note="Confirmed benign: PSI within investigate band, AUC stable. No action.",
                user=rev,
            )
        q3 = [a for a in alerts if a.monitoring_batch_id == batches[2].id and a.severity == "high"]
        if q3:
            monitoring.update_alert(
                db,
                q3[0],
                status="investigating",
                note="Material DTI and rate shift; assessing whether retraining is warranted.",
                user=ds,
            )

        # v1.1.0 - complete, pending review.
        log("v1.1.0: complete package, pending review")
        v110 = registry.register_version(
            db,
            training_run_id=run_b.id,
            semantic_version="pd-credit-v1.1.0",
            model_type="champion",
            description="Re-tuned champion candidate with stronger regularisation.",
            user=ds,
        )
        registry.validate_version(db, v110, ds)
        registry.set_narrative(
            db,
            v110,
            {
                **NARRATIVE,
                "changes": "- Stronger regularisation (learning_rate 0.03, 200 iterations) after v1.0.0 monitoring drift.\n- Same feature set and preprocessing as v1.0.0.",
            },
            ds,
        )
        registry.replace_controls(db, v110, CONTROLS, ds)
        registry.submit_review(db, v110, ds)

        # v1.2.0 - incomplete; submission blocked.
        log("v1.2.0: incomplete package, submission blocked by the readiness gate")
        v120 = registry.register_version(
            db,
            training_run_id=run_b.id,
            semantic_version="pd-credit-v1.2.0",
            model_type="baseline",
            description="Baseline logistic candidate registered without governance package.",
            user=ds,
        )
        registry.validate_version(db, v120, ds)
        registry.replace_controls(db, v120, CONTROLS[:2], ds)
        try:
            registry.submit_review(db, v120, ds)
        except Problem as exc:
            log(f"  blocked as expected: {exc.detail}")
        ids: dict[str, str] = {}
        if UCI_RAW.exists():
            log("UCI 350: register source, import, train, v2.0.0 approve + monitor (licensed public data)")
            lineage.register_source(db, UCI_SOURCE, ds)
            uci_snap = lineage.import_snapshot(
                db,
                source_id=UCI_SOURCE["id"],
                file_path=str(UCI_RAW.relative_to(ROOT)),
                as_of_date="2005-09-30",
                purpose="training",
                user=ds,
            )
            batch_dir = UCI_RAW.parent / "monitoring"
            if not batch_dir.exists():
                import subprocess

                subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_uci_batches.py")], check=True)
            uci_batches = [
                lineage.import_snapshot(
                    db,
                    source_id=UCI_SOURCE["id"],
                    file_path=str(p.relative_to(ROOT)),
                    as_of_date=p.stem.replace("batch_", ""),
                    purpose="monitoring",
                    user=ds,
                )
                for p in sorted(batch_dir.glob("batch_*.csv"))
            ]
            run_c = training.create_run(db, snapshot_id=uci_snap.id, seed=42, hyperparams=None, user=ds)
            training.execute_run(run_c.id)
            db.expire_all()
            v200 = registry.register_version(
                db,
                training_run_id=run_c.id,
                semantic_version="pd-credit-v2.0.0",
                model_type="champion",
                description="Champion PD model on the licensed UCI 350 credit-card dataset.",
                user=ds,
            )
            registry.validate_version(db, v200, ds)
            registry.set_narrative(db, v200, UCI_NARRATIVE, ds)
            registry.replace_controls(db, v200, CONTROLS, ds)
            registry.submit_review(db, v200, ds)
            registry.decide(
                db,
                v200,
                "approve",
                "Licensed public data (CC BY 4.0) with citation; stratified-split limitation documented; package complete.",
                rev,
            )
            for snap_b in uci_batches:
                monitoring.run_batch(db, v200, snapshot_id=snap_b.id, user=ds)
            ids["v200"] = v200.id
        else:
            log(
                "UCI 350 raw file not present; skipping the real-data lineage (see docs/data-sources/uci-credit-default-2005.md)"
            )
        n_alerts = len(monitoring.alerts_for(db, v100))
        open_alerts = db.query(Alert).filter(Alert.status != "resolved").count()
        log(f"done: alerts={n_alerts} open={open_alerts}")
        return {
            "v100": v100.id,
            "v110": v110.id,
            "v120": v120.id,
            "run_a": run_a.id,
            "run_b": run_b.id,
            "snapshot": snap.id,
        }
    finally:
        db.close()


if __name__ == "__main__":
    seed(reset="--keep" not in sys.argv)

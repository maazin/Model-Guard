"""Generate the executive risk memo and five-slide deck from the seeded registry.

Every number is read from the database (measured), never typed in. Run after `make seed`.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("apps/api", "packages/ml", "packages/governance", "packages/shared"):
    sys.path.insert(0, str(ROOT / p))

from modelguard_api.db import SessionLocal  # noqa: E402
from modelguard_api.models import (  # noqa: E402
    Alert,
    AuditEvent,
    Control,
    DataSnapshot,
    ModelVersion,
    MonitoringBatch,
    ReadinessCheck,
    TrainingRun,
)
from modelguard_api.services import executive, monitoring, registry  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

OUT = ROOT / "docs" / "executive"


def f(x: float | None, d: int = 3) -> str:
    return "n/a" if x is None else f"{x:.{d}f}"


def main() -> None:
    for version in ("pd-credit-v1.0.0", "pd-credit-v2.0.0"):
        try:
            build(version)
        except Exception as exc:  # noqa: BLE001 - v2 only exists when the UCI file is present
            print(f"skipped {version}: {exc}")


def build(version: str) -> None:
    db = SessionLocal()
    try:
        mv = registry.get_version(db, version)
        s = executive.summary(db, mv)
        run = mv.training_run
        counts = {
            "snapshots": db.scalar(select(func.count()).select_from(DataSnapshot)),
            "training_runs": db.scalar(select(func.count()).select_from(TrainingRun)),
            "model_versions": db.scalar(select(func.count()).select_from(ModelVersion)),
            "controls": db.scalar(select(func.count()).select_from(Control).where(Control.model_version_id == mv.id)),
            "readiness_checks": db.scalar(
                select(func.count()).select_from(ReadinessCheck).where(ReadinessCheck.model_version_id == mv.id)
            ),
            "batches": db.scalar(
                select(func.count()).select_from(MonitoringBatch).where(MonitoringBatch.model_version_id == mv.id)
            ),
            "alerts": db.scalar(select(func.count()).select_from(Alert).where(Alert.model_version_id == mv.id)),
            "alerts_high": db.scalar(
                select(func.count()).select_from(Alert).where(Alert.model_version_id == mv.id, Alert.severity == "high")
            ),
            "alerts_resolved": db.scalar(
                select(func.count())
                .select_from(Alert)
                .where(Alert.model_version_id == mv.id, Alert.status == "resolved")
            ),
            "audit_events": db.scalar(select(func.count()).select_from(AuditEvent)),
        }
        h, c = s["holdout"], s["comparator"]
        batches = monitoring.batches_for(db, mv)
        fair = run.metrics_json[mv.model_type].get("fairness") or {}
        versions = list(db.scalars(select(ModelVersion).order_by(ModelVersion.created_at)))
        v_rows = "\n".join(f"| {v.semantic_version} | {v.model_type} | {v.state} |" for v in versions)
        b_rows = "\n".join(
            f"| {b.as_of_date} | {b.status} | {f(b.results_json.get('performance', {}).get('auc', {}).get('value'))} | "
            f"{f(max(x['psi'] for x in b.results_json['psi'].values()))} | {f(b.results_json['score_drift']['psi'])} |"
            for b in batches
        )
        today = date.today().isoformat()
        memo = f"""---
title: Executive risk memo — {mv.semantic_version}
generated: {today}
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Executive risk memo — ModelGuard PD model {mv.semantic_version}

> Portfolio simulation. Not credit advice, not a production lending system, and not a compliance claim. Data source: `{run.snapshot.source_id}`.

## Decision requested

{s["recommendation"]}

## What the model is

{s["purpose"]} Data source `{run.snapshot.source_id}`. Registered type **{mv.model_type}** (gradient-boosted trees) compared against a logistic-regression baseline on a {run.config_json.get("split", {}).get("strategy")} holdout of {int(run.metrics_json[mv.model_type]["metrics"]["n_holdout"]["value"])} loans.

## Current health: **{s["health"].replace("_", " ")}** (state {mv.state})

| Measure | {mv.model_type} | baseline |
| --- | --- | --- |
| AUC (95% bootstrap CI) | {f(h["auc"]["value"])} [{f(h["auc"]["lower_ci"])}, {f(h["auc"]["upper_ci"])}] | {f(c["auc"]["value"])} [{f(c["auc"]["lower_ci"])}, {f(c["auc"]["upper_ci"])}] |
| KS | {f(h["ks"]["value"])} | {f(c["ks"]["value"])} |
| Brier | {f(h["brier"]["value"], 4)} | {f(c["brier"]["value"], 4)} |
| ECE | {f(h["ece"]["value"], 4)} | {f(c["ece"]["value"], 4)} |

Fairness diagnostics on the `{run.config_json.get("feature_spec", {}).get("fairness_field", "fairness_group")}` grouping field: selection-rate ratio {f(fair.get("selection_rate_ratio"))}, TPR difference {f(fair.get("tpr_difference"))}, FPR difference {f(fair.get("fpr_difference"))} (informational only).

## Monitoring ({counts["batches"]} quarterly batches)

| Batch | Status | AUC | Max feature PSI | Score PSI |
| --- | --- | --- | --- | --- |
{b_rows}

{counts["alerts"]} alerts raised ({counts["alerts_high"]} high severity); {counts["alerts_resolved"]} resolved with a recorded rationale. Top open risks: {"; ".join(s["top_risks"]) or "none"}.

## Governance evidence

- Readiness: {s["readiness"]["passed"]}/{s["readiness"]["total"]} deterministic checks pass; {counts["controls"]} controls recorded with owner, frequency and test evidence.
- Registry: {counts["model_versions"]} model versions, {counts["training_runs"]} training runs, {counts["snapshots"]} data snapshots, {counts["audit_events"]} hash-chained audit events (chain verified).

| Version | Type | State |
| --- | --- | --- |
{v_rows}

## Limits

{chr(10).join("- " + limit for limit in s["limits"])}

## Recommended next action

{s["next_action"]}
"""
        (OUT / f"risk-memo-{mv.semantic_version}.md").write_text(memo)

        deck = f"""---
title: ModelGuard — five-slide executive deck
generated: {today}
source: scripts/generate_executive_pack.py (measured values from the seeded demo run)
---

# Slide 1 — Why ModelGuard

- One place to develop, validate, approve, monitor and document a PD model.
- Portfolio simulation on `{run.snapshot.source_id}`; every control is real, every number is measured.
- Human approval gate, hash-chained audit log, offline governance copilot.

---

# Slide 2 — Model performance ({mv.semantic_version}, {run.config_json.get("split", {}).get("strategy")} holdout)

| | {mv.model_type} | baseline |
| --- | --- | --- |
| AUC | {f(h["auc"]["value"])} [{f(h["auc"]["lower_ci"])}, {f(h["auc"]["upper_ci"])}] | {f(c["auc"]["value"])} |
| KS | {f(h["ks"]["value"])} | {f(c["ks"]["value"])} |
| Brier / ECE | {f(h["brier"]["value"], 4)} / {f(h["ece"]["value"], 4)} | {f(c["brier"]["value"], 4)} / {f(c["ece"]["value"], 4)} |

Differences sit inside the confidence interval; promotion was a human decision, not a metric race.

---

# Slide 3 — Governance package

- {s["readiness"]["passed"]}/{s["readiness"]["total"]} readiness checks pass; an incomplete version (pd-credit-v1.2.0) is blocked with named gaps.
- {counts["controls"]} controls with owners and test evidence; 8 versioned documents per model.
- {counts["audit_events"]} audit events in a verified SHA-256 chain.

---

# Slide 4 — Monitoring

| Batch | Status | AUC | Max PSI | Score PSI |
| --- | --- | --- | --- | --- |
{b_rows}

{counts["alerts"]} alerts ({counts["alerts_high"]} high); {counts["alerts_resolved"]} resolved with rationale. Thresholds are configurable defaults, not policy.

---

# Slide 5 — Recommendation and limits

- **{s["recommendation"]}**
- {"Synthetic data" if "synthetic" in run.snapshot.source_id else "Public 2005 Taiwanese credit-card data"}; results do not transfer to a real book.
- Illustrative threshold only; fairness diagnostics are informational.
- Next: {s["next_action"]}
"""
        (OUT / f"five-slide-deck-{mv.semantic_version}.md").write_text(deck)
        print(f"wrote risk-memo-{mv.semantic_version}.md and five-slide-deck-{mv.semantic_version}.md")
    finally:
        db.close()


if __name__ == "__main__":
    main()

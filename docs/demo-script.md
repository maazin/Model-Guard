# Demo script (about 3 minutes)

Prerequisite: `make docker-up` (dashboard on http://localhost:8080) or `make setup && make seed && make dev`
(dashboard on http://localhost:5173). Everything below is seeded; no API key needed.

| Time | Where | What to show | Say |
| --- | --- | --- | --- |
| 0:00 | Portfolio | Four versions with lifecycle state, health, next action | "Two models are live and monitored — one on real CC BY 4.0 data — one is waiting for review, one is blocked." |
| 0:15 | pd-credit-v2.0.0 → Validation | Real-data holdout: champion 0.789 vs baseline 0.742, fairness on `sex` | "Licensed public data, stratified split documented as a limitation." |
| 0:30 | pd-credit-v1.0.0 → Version | Lineage block: source, license, checksum, seed, git SHA, split; feature importance | "Every run is reproducible from what you see here." |
| 1:00 | Validation | Holdout table with bootstrap CIs, ROC, calibration, threshold analysis, fairness, KS test | "Champion vs baseline are inside each other's CI — promotion was a human call." |
| 1:30 | Monitoring | Three quarterly batches; Q3 PSI alerts; open/resolve an alert with a note | "Deliberately shifted batch trips PSI; every resolution is audit-logged." |
| 2:00 | pd-credit-v1.2.0 → Governance (as Data scientist) | Click *Submit for review* → 409 with every missing item | "The gate names each gap; it never just says no." |
| 2:20 | pd-credit-v1.1.0 → Governance (as Model risk reviewer) | Enter rationale → Approve; audit log grows; chain verify endpoint | "Only the reviewer role can do this, and the API enforces it." |
| 2:45 | Governance → Copilot | Ask "What evidence is missing before this version can be approved?" | "Offline rule-based provider, cites the exact document sections." |
| 3:00 | Executive | One-screen summary and `docs/executive/risk-memo.md` | "Generated from measured values only." |

Reset the demo at any time with `make seed` (or `docker compose down -v && make docker-up`).

## Walkthrough video outline

1. (0:00–0:20) Problem: model lifecycle evidence is scattered; ModelGuard puts it in one governed flow.
2. (0:20–1:10) Data → training → validation with statistics (CIs, calibration, hypothesis test, fairness).
3. (1:10–2:00) Registry, readiness gate blocking an incomplete version, reviewer approval, hash-chained audit.
4. (2:00–2:40) Monitoring drift alerts and resolution workflow.
5. (2:40–3:00) Copilot with citations, executive memo, and the limits of a synthetic portfolio project.

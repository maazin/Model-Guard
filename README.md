# ModelGuard - governed credit-risk model lifecycle platform

> **Portfolio simulation.** ModelGuard trains, validates, approves, monitors and documents a probability-of-default
> (PD) model on the **CC BY 4.0-licensed UCI "Default of Credit Card Clients" dataset** and on an in-repo
> **synthetic** loan fixture. It is **not a lending system, not credit advice, and makes no claim of compliance with
> any regulation or any bank's governance framework.** Nothing here connects to a real bank, bureau, customer or
> borrower.

ModelGuard brings four normally-fragmented workflows into one local-first application:

1. **Train and evaluate** an explainable PD model (logistic baseline vs. gradient-boosted champion) on a temporal holdout with bootstrap confidence intervals, calibration, threshold analysis, feature importance, a documented hypothesis test and fairness diagnostics.
2. **Register immutable model versions** with lineage (source → snapshot → training run → version), eight versioned governance documents, a control matrix, a deterministic **readiness gate** that names every missing piece of evidence, a human-only approval step, and a **hash-chained, append-only audit log**.
3. **Monitor** dated batches for data quality, feature/score drift (PSI), calibration and performance, with an alert → investigate → resolve workflow.
4. Ask a **retrieval-grounded governance copilot** what is missing before approval. It reads only that version's approved documents, cites document sections, returns a validated JSON structure, and works fully offline with a deterministic rule-based provider.

![Monitoring page](docs/screenshots/monitoring.png)

## Quick start

**Docker (PostgreSQL 16, one command):**

```bash
docker compose up --build
```

Dashboard: http://localhost:8080 · API + OpenAPI: http://localhost:8000/docs. The API container applies migrations and, if the registry is empty, seeds the demo (three model versions, three monitoring batches, alerts) — about 20 s.

**Local (SQLite, hot reload):**

```bash
make setup      # uv venv + Python deps + npm install
make seed       # migrations + demo registry
make dev        # API on :8000 and dashboard on :5173
```

**Real data (optional, recommended):**

```bash
make fetch-uci   # prints the CC BY 4.0 terms, asks you to confirm, downloads 5.3 MB into git-ignored data/sources/
make seed        # now also builds pd-credit-v2.0.0 on the real data
```

Requirements: Python 3.12+ (uv installs 3.13), Node 20, Docker (optional). No API key is needed; set `MODELGUARD_LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in `.env` to try the hosted copilot provider (it still never sees loan rows).

Acting as a user: the dashboard's **Acting as** menu switches between the seeded demo users `data_scientist`, `reviewer` and `risk_leader`; API calls send the `X-Demo-User` header, and every authorisation check is enforced server-side.

## What to look at (the PRD's success criteria)

| # | Criterion | Where |
| --- | --- | --- |
| 1 | Dataset source, license, schema, checksums, data-quality results | Version page → Lineage; `docs/data-sources/synthetic-loans-v1.md`; `GET /api/v1/snapshots/{id}` |
| 2 | Reproducible training, champion vs. baseline | Validation page → holdout table; `training_runs.config_json` stores seed, features, hyperparameters, package versions, data checksum, git SHA |
| 3 | AUC, KS, Brier, calibration, CIs, fairness | Validation page (ROC, calibration curve, confusion matrix, threshold analysis, fairness table, KS test) |
| 4 | Model card and validation report tied to one immutable version | Version page → Model card; Governance page → Documents (download as Markdown) |
| 5 | Incomplete version blocked with specific missing evidence | Governance page for `pd-credit-v1.2.0` as *Data scientist* → **Submit for review** → 409 listing every gap |
| 6 | Human approval as reviewer, append-only audit event | Governance page for `pd-credit-v1.1.0` as *Model risk reviewer* → rationale → **Approve**; Version page → Audit log; `GET /api/v1/audit-events/verify` |
| 7 | Dated monitoring batch with quality, drift, calibration, performance alerts | Monitoring page for `pd-credit-v1.0.0` (Q1 stable → Q2 investigate → Q3 alerts); resolve an alert with a note |
| 8 | Copilot returns a structured, cited answer | Governance page → Governance copilot; `POST /api/v1/model-versions/{id}/copilot/query` |
| 9 | Tests and CI | `make ci` (lint, types, tests, secrets scan); `.github/workflows/ci.yml` also runs Postgres migrations, Playwright e2e, gitleaks and Docker builds |

A three-minute walkthrough is in [docs/demo-script.md](docs/demo-script.md).

## Measured results (seeded demo run)

All numbers below are read from the seeded database by `make executive-pack` / `make test` — none are typed in. Re-run to refresh them; they will change if the fixture generator or model code changes.

**Real data — `pd-credit-v2.0.0` on UCI 350 (30,000 cardholders, stratified 18,000 / 6,000 / 6,000 split):**

| Item | Value |
| --- | --- |
| Champion (`HistGradientBoosting`) holdout | AUC **0.789** [0.776, 0.804] · KS 0.438 · Brier 0.1318 · ECE 0.0111 |
| Baseline (logistic) holdout | AUC 0.742 [0.726, 0.758] · KS 0.415 · Brier 0.1404 · ECE 0.0271 |
| Top permutation importances | `pay_status_max` 0.048 · `pay_status_recent` 0.026 · `bill_amt_mean` 0.017 · `utilization_recent` 0.012 |
| Fairness diagnostics (`sex`, never a feature) | selection-rate ratio 0.873 · TPR diff 0.020 · FPR diff 0.026 |
| Monitoring (3 generated stress batches) | stable → mild (max PSI 0.34) → strong (max PSI 0.82, score PSI 0.36, AUC 0.740); 13 alerts (7 high) |

**Synthetic fixture — `pd-credit-v1.x` (6,000 loans over 24 monthly cohorts, temporal split 3,437 / 1,262 / 1,301):**

| Item | Value |
| Champion (`HistGradientBoosting`) holdout | AUC **0.764** [0.723, 0.801] · KS 0.409 [0.357, 0.488] · Brier 0.0832 · ECE 0.0086 |
| Baseline (logistic) holdout | AUC 0.771 [0.732, 0.809] · KS 0.410 · Brier 0.0828 · ECE 0.0134 |
| Fairness diagnostics (synthetic group) | selection-rate ratio 0.857 · TPR diff 0.072 · FPR diff 0.010 |
| Registry (whole demo) | 4 model versions (2 MONITORING, 1 PENDING_REVIEW, 1 VALIDATED-blocked), 3 training runs, 2 data sources, 8 snapshots, 8 readiness checks, 6 controls, 8 documents per version |
| Readiness gate | complete versions 8/8 pass; the incomplete version fails 6 of 7 review-blocking checks with 22 named gaps |
| Monitoring | 3 batches; 8 induced alerts (4 high, 4 medium): PSI on `debt_to_income` 1.27, `interest_rate` 3.43, `employment_length` 0.35, score PSI 1.41; 1 resolved, 1 investigating |
| Audit | 189 hash-chained events on the full seed; chain verifies |
| Copilot | rule-based provider scores **8/8 (100%)** on the hand-authored completeness set (`tests/fixtures/copilot_eval.json`); hosted providers not measured (no key in CI) |
| Tests | 119 pytest (99 unit incl. the copilot eval and UCI adapter tests + 20 integration; 1 hosted-provider eval skipped without a key) + 5 Playwright e2e; **93% line coverage** overall (lifecycle and audit modules 100%) |
| Latency (local SQLite, p50 / p95) | version detail 7 / 9 ms · monitoring 8 / 8 ms · executive summary 38 / 40 ms · copilot query 51 / 65 ms · portfolio 107 / 198 ms (re-runs the readiness engine incl. secrets scan) |
| Dashboard load (Vite dev, network idle) | 0.6–0.9 s per page |

Source: `docs/executive/measured-demo-metrics.json`, `docs/executive/risk-memo-<version>.md`, `docs/executive/five-slide-deck-<version>.md`.

**Attribution:** Yeh, I. (2009). *Default of Credit Card Clients* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C55S3H (CC BY 4.0). See [docs/data-sources/uci-credit-default-2005.md](docs/data-sources/uci-credit-default-2005.md).

## Architecture

```mermaid
flowchart LR
  UI[React dashboard<br/>Vite · Tailwind · React Query · Recharts] -->|/api/v1 · X-Demo-User| API[FastAPI<br/>RFC 7807 errors · OpenAPI]
  API --> PG[(PostgreSQL 16<br/>registry · metrics · docs · audit chain · alerts)]
  API --> ML[modelguard_ml<br/>metrics · drift · fairness · training pipeline]
  API --> GOV[modelguard_governance<br/>lifecycle · readiness · audit · documents · copilot]
  GOV --> IDX[Local TF-IDF section index<br/>approved docs only]
  ML --> ART[(artifacts/<br/>joblib pipelines · metrics.json)]
  FIX[(data/fixtures<br/>synthetic CSVs)] --> API
```

Lifecycle: `DRAFT → VALIDATED → PENDING_REVIEW → APPROVED → MONITORING → RETIRED`, with `REJECTED` reachable from review or approval and `REOPEN` back to draft. Only `reviewer` can approve/reject/retire; only `data_scientist` can train, validate, edit narrative/controls or submit; nothing is modifiable after submission; every transition is an audit event.

Key decisions are recorded in [docs/architecture/decisions](docs/architecture/decisions/README.md): dataset & license (UCI 350 under CC BY 4.0, owner-confirmed, plus the synthetic fixture; each source has its own `FeatureSpec`), HistGradientBoosting over XGBoost, temporal split with a documented stratified fallback, target/leakage controls (protected characteristics excluded from features), permutation importance instead of SHAP, TF-IDF retrieval with a mandatory offline provider, and configurable (not policy) monitoring thresholds.

## Repository layout

```
apps/api/        FastAPI app, SQLAlchemy models, Alembic migrations, services, demo seed
apps/web/        React + TypeScript dashboard, Playwright e2e
packages/ml/     metrics, drift, fairness, data quality, splits, training, synthetic data, adapters
packages/governance/  lifecycle state machine, readiness engine, audit chain, documents, copilot
packages/shared/ hashing, constants, JSON sanitising
data/fixtures/   synthetic training set + 3 monitoring batches      data/sources/  (git-ignored) licensed raw files
docs/            ADRs, data-source docs, governance templates, generated per-version docs, executive pack, screenshots
tests/           unit, integration (SQLite or Postgres), copilot eval fixtures
infra/docker/    Dockerfiles, nginx config, entrypoint (migrate + seed)
```

## API

All endpoints live under `/api/v1` and are documented at `/docs`. Highlights: `POST /data-sources`, `POST /snapshots/import`, `POST /training-runs`, `POST /model-versions`, `POST /model-versions/{id}/validate | submit-review | decision | retire | reopen`, `PUT /model-versions/{id}/narrative | controls`, `GET /model-versions/{id}/documents/{type}[/download]`, `POST /model-versions/{id}/monitoring-batches`, `GET /model-versions/{id}/monitoring`, `PATCH /model-versions/{id}/alerts/{alert_id}`, `POST /model-versions/{id}/copilot/query`, `GET /executive-summary/{id}`, `GET /portfolio`, `GET /audit-events[/verify]`.

## Development

```bash
make test          # pytest with coverage (SQLite, offline)
make lint          # ruff + eslint          make typecheck   # mypy + tsc
make e2e           # Playwright (needs a seeded API on :8000 and `npx playwright install chromium`)
make secrets-scan  # local scan; CI also runs gitleaks
make executive-pack  # regenerate memo + deck from the database
make fixtures      # regenerate synthetic CSVs deterministically
```

Conventions for contributors (and for Claude Code) are in [CLAUDE.md](CLAUDE.md).

## Ethical boundaries

No PII beyond what the CC BY 4.0 dataset publishes (and `loan_id` is a hash), no scraped or unlicensed data, protected characteristics never used as features, no real lending decisions, no automated approvals, no borrower-level rows in the UI/logs/prompts, and no compliance claims. See the PRD's non-goals, ADR-0001 and ADR-0004.

## License

MIT. The synthetic fixture is generated in-repo and carries the same license.

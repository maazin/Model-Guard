# CLAUDE.md — conventions for working in this repository

ModelGuard is a **portfolio simulation** of a governed credit-risk (PD) model lifecycle. It is not a lending
system, not credit advice, and makes no regulatory-compliance claims. Keep that framing in every artifact.

## Ground rules

- **No fabricated metrics.** Every number in docs, memos, slides or README comes from a measured run
  (`scripts/generate_executive_pack.py` reads the database). Never type a metric by hand.
- **No secrets.** Nothing in `.env` is committed; `make secrets-scan` and gitleaks run in CI. API keys are
  optional and only enable the hosted copilot providers.
- **No raw borrower rows** in logs, prompts, documents, or the UI. `loan_id` values are pseudonymous hashes and
  never rendered. The copilot rejects questions containing them.
- **Tests before UI claims.** A feature is done when its unit/integration test passes; the dashboard only
  displays what the API already proves.
- **Small commits**, one concern each, imperative subject line.
- **Human approval is never automated.** Only a `reviewer` may approve/reject, and only via `POST .../decision`.
- **Do not invent dataset-license or policy facts.** Real datasets need a human to confirm the license
  (ADR-0001); thresholds are configurable defaults (ADR-0007).

## Layout

```
apps/api/modelguard_api      FastAPI app: routers/, services/, models.py, seed.py, alembic/
apps/web                     React + TypeScript + Vite + Tailwind dashboard
packages/ml/modelguard_ml    metrics, drift, fairness, data quality, training pipeline, synthetic data
packages/governance/...      lifecycle state machine, readiness engine, audit hash chain, documents, copilot
packages/shared/...          hashing, constants, JSON sanitising
docs/                        ADRs, data-source docs, governance templates, generated model docs, executive pack
tests/unit, tests/integration, tests/e2e (Playwright in apps/web/e2e)
```

## Commands

`make setup` · `make seed` · `make api` / `make web` (or `make dev`) · `make test` · `make lint` · `make typecheck`
· `make e2e` · `make docker-up` · `make executive-pack`

## Style

Python 3.12+, Ruff (120 cols), mypy on all packages, Pydantic v2, SQLAlchemy 2 typed mappings. Frontend: strict
TypeScript, React Query for server state, Recharts for charts, status colours always paired with a text label.

.PHONY: help setup dev api web seed migrate test test-unit test-integration e2e lint format typecheck secrets-scan ci docker-up docker-down executive-pack fixtures clean

PY := .venv/bin/python
UV := uv

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv, install Python + web dependencies
	$(UV) venv --python 3.13 -q || true
	$(UV) pip install -q -e ".[dev]"
	cd apps/web && npm install --no-audit --no-fund

migrate: ## Apply database migrations
	cd apps/api && ../../.venv/bin/alembic upgrade head

seed: migrate ## Seed the demo registry (three versions, monitoring batches, alerts)
	$(PY) apps/api/modelguard_api/seed.py

fixtures: ## Regenerate synthetic fixture CSVs
	$(PY) scripts/generate_fixtures.py

api: ## Run the API on :8000 (SQLite)
	.venv/bin/uvicorn modelguard_api.main:app --reload --port 8000

web: ## Run the dashboard dev server on :5173
	cd apps/web && npm run dev

dev: ## Migrate, seed if empty, then run API + web together
	@$(MAKE) migrate
	@$(PY) -c "from sqlalchemy import select; from modelguard_api.db import SessionLocal; from modelguard_api.models import ModelVersion; import sys; sys.exit(0 if SessionLocal().scalar(select(ModelVersion).limit(1)) else 1)" || $(MAKE) seed
	@(.venv/bin/uvicorn modelguard_api.main:app --port 8000 & echo $$! > .api.pid); cd apps/web && npm run dev; kill `cat ../../.api.pid`

test: ## Unit + integration tests with coverage
	$(PY) -m pytest -q --cov --cov-report=term-missing:skip-covered --cov-report=xml

test-unit: ## Unit tests only
	$(PY) -m pytest -q tests/unit

test-integration: ## Integration tests only
	$(PY) -m pytest -q tests/integration

e2e: ## Playwright end-to-end tests (needs `make seed` and a browser install)
	cd apps/web && npx playwright test

lint: ## Ruff lint + web eslint
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	cd apps/web && npm run lint --silent

format: ## Auto-format Python
	.venv/bin/ruff format . && .venv/bin/ruff check . --fix

typecheck: ## mypy + tsc
	.venv/bin/mypy
	cd apps/web && npx tsc -b --noEmit

secrets-scan: ## Local secrets scan (CI runs gitleaks)
	$(PY) scripts/secrets_scan.py

executive-pack: ## Generate executive memo + deck from the seeded run (measured values only)
	$(PY) scripts/generate_executive_pack.py

ci: lint typecheck test secrets-scan ## Everything CI runs (except docker build)

docker-up: ## Build and start Postgres + API + web (dashboard on :8080)
	docker compose up --build -d
	@echo "API: http://localhost:8000/docs  Dashboard: http://localhost:8080"

docker-down: ## Stop containers (keeps volumes)
	docker compose down

clean: ## Remove local DB, artifacts and caches
	rm -rf modelguard.db artifacts/runs .pytest_cache .mypy_cache .ruff_cache htmlcov coverage.xml

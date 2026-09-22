#!/bin/sh
set -e
cd /app/apps/api
echo "Running migrations..."
alembic upgrade head
cd /app
if [ "${MODELGUARD_SEED_ON_START:-true}" = "true" ]; then
  python - <<'PY'
from sqlalchemy import select, text
from modelguard_api.db import SessionLocal
from modelguard_api.models import ModelVersion
with SessionLocal() as db:
    n = db.scalar(select(ModelVersion).limit(1))
if n is None:
    print("Empty registry: seeding demo data (takes ~20s)...")
    from modelguard_api.seed import seed
    seed(reset=False)
else:
    print("Registry already seeded; skipping.")
PY
fi
exec "$@"

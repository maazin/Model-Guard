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
import os
with SessionLocal() as db:
    n = db.scalar(select(ModelVersion).limit(1))
reset = os.environ.get("MODELGUARD_RESET_ON_START", "false").lower() == "true"
if n is None or reset:
    print("Seeding demo data (reset=%s, takes ~20s)..." % reset)
    from modelguard_api.seed import seed
    seed(reset=reset)
else:
    print("Registry already seeded; skipping.")
PY
fi
exec "$@"

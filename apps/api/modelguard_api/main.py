from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from modelguard_api.config import get_settings
from modelguard_api.errors import install_error_handlers
from modelguard_api.routers import data, misc, model_versions, training

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="ModelGuard API",
    version="0.1.0",
    description=(
        "Governed credit-risk (PD) model lifecycle platform. **Portfolio simulation only** — "
        "not a lending system, not credit advice, and not represented as compliant with any regulation."
    ),
)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
install_error_handlers(app)
app.include_router(data.router)
app.include_router(training.router)
app.include_router(model_versions.router)
app.include_router(misc.router)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}

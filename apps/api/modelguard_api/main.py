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
def health() -> dict[str, str | bool]:
    return {"status": "ok", "env": settings.env, "public_demo": settings.public_demo}


if settings.serve_web_dir and settings.serve_web_dir.exists():
    # Single-container deployment: the built dashboard is served by the API process, with an SPA fallback.
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    web_dir = settings.serve_web_dir
    app.mount("/assets", StaticFiles(directory=web_dir / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        candidate = web_dir / full_path
        if full_path and candidate.is_file() and candidate.resolve().is_relative_to(web_dir.resolve()):
            return FileResponse(candidate)
        return FileResponse(web_dir / "index.html")

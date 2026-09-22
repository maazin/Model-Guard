from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODELGUARD_", env_file=ROOT / ".env", extra="ignore")

    env: str = "local"
    database_url: str = f"sqlite:///{ROOT / 'modelguard.db'}"
    artifact_dir: Path = ROOT / "artifacts"
    docs_dir: Path = ROOT / "docs"
    fixture_dir: Path = ROOT / "data" / "fixtures"
    llm_provider: str = "rule_based"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:8080"]
    n_bootstrap: int = 300
    serve_web_dir: Path | None = None  # set to the built dashboard (apps/web/dist) to serve API + UI from one process
    public_demo: bool = False  # adds a banner hint to /health and reseeds on start when combined with reset_on_start
    reset_on_start: bool = False


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Managed Postgres providers hand out postgres:// URLs; SQLAlchemy needs the driver-qualified scheme.
    if s.database_url.startswith(("postgres://", "postgresql://")) and "+psycopg" not in s.database_url:
        s.database_url = "postgresql+psycopg://" + s.database_url.split("://", 1)[1]
    return s

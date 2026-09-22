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


@lru_cache
def get_settings() -> Settings:
    return Settings()

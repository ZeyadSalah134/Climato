"""Application configuration.

All configuration is environment-driven so the same code can run locally,
in Docker Compose, or on a managed Python host without code changes.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent

IS_VERCEL = bool(os.environ.get("VERCEL"))
DEFAULT_DB_PATH = "/tmp/earthtrend.db" if IS_VERCEL else (REPO_ROOT / "data" / "earthtrend.db").as_posix()
DEFAULT_CACHE_DIR = Path("/tmp/data/cache") if IS_VERCEL else REPO_ROOT / "data" / "cache"
DEFAULT_DEMO_DIR = Path("/tmp/data/samples") if IS_VERCEL else REPO_ROOT / "data" / "samples"


class Settings(BaseSettings):
    """Runtime settings for the EarthTrend backend."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    app_name: str = "EarthTrend API"
    app_version: str = "1.0.0"
    analysis_engine_version: str = "1.0.0"
    environment: str = Field(default="production" if IS_VERCEL else "development")
    debug: bool = Field(default=False)

    # --- HTTP server -------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000
    api_prefix: str = "/api/v1"

    # --- CORS --------------------------------------------------------------
    # Comma separated list. "*" allows any origin (development default).
    cors_origins: str = "*"

    # --- NASA POWER --------------------------------------------------------
    power_base_url: str = "https://power.larc.nasa.gov/api/temporal"
    power_community: str = "SB"  # SB = Sustainable Buildings / agroclimatology
    power_timeout_seconds: float = 30.0
    power_max_retries: int = 3
    power_retry_backoff_seconds: float = 1.5

    # --- Caching -----------------------------------------------------------
    cache_dir: Path = Field(default_factory=lambda: DEFAULT_CACHE_DIR)
    cache_enabled: bool = True
    cache_ttl_seconds: int = 60 * 60 * 24 * 7  # one week

    # --- Demo / offline mode ----------------------------------------------
    # When true the API will fall back to bundled, provenance-documented data
    # snapshots if NASA POWER cannot be reached. Responses are always marked.
    allow_demo_fallback: bool = True
    demo_data_dir: Path = Field(default_factory=lambda: DEFAULT_DEMO_DIR)

    # --- Persistence -------------------------------------------------------
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DB_PATH}")

    # --- Rate limiting -----------------------------------------------------
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    # --- Geospatial (optional) --------------------------------------------
    geospatial_enabled: bool = True
    nasadem_path: Path | None = None
    worldcover_path: Path | None = None

    @field_validator("cors_origins")
    @classmethod
    def _strip_origins(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def ensure_directories(self) -> None:
        """Create runtime directories that must exist before use."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.demo_data_dir.mkdir(parents=True, exist_ok=True)
            (REPO_ROOT / "data").mkdir(parents=True, exist_ok=True)
        except OSError:
            tmp_cache = Path("/tmp/data/cache")
            tmp_cache.mkdir(parents=True, exist_ok=True)
            self.cache_dir = tmp_cache
            tmp_demo = Path("/tmp/data/samples")
            tmp_demo.mkdir(parents=True, exist_ok=True)
            self.demo_data_dir = tmp_demo


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings


settings = get_settings()

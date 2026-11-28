"""Typed application settings from environment variables (NFR-PORT-002).

Every value has a safe local default and is documented in the repository's
`.env.example`. A repository-root `.env` file is read when it exists; real
environment variables take precedence over it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
SHARED_ENVIRONMENTS = frozenset({"staging", "production"})

Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    """Backend configuration; invalid values stop start-up with a validation error."""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # the shared .env also holds frontend and later-milestone keys
        frozen=True,
    )

    app_env: Environment = "development"
    app_debug: bool = False
    backend_host: str = "127.0.0.1"
    backend_port: int = Field(default=8000, ge=1, le=65535)
    shutdown_timeout_seconds: int = Field(default=20, ge=1, le=120)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    # Feature flags (FR-PLAT-013, ADR-0009): read from FEATURE_<NAME>, off by default.
    feature_ai_assistant: bool = False
    feature_external_product_sources: bool = False
    feature_notifications: bool = False

    @field_validator("log_level", "log_format", mode="before")
    @classmethod
    def _normalize_case(cls, value: object, info: ValidationInfo) -> object:
        if not isinstance(value, str):
            return value
        return value.strip().upper() if info.field_name == "log_level" else value.strip().lower()

    @model_validator(mode="after")
    def _no_debug_in_shared_environments(self) -> Settings:
        if self.app_debug and self.app_env in SHARED_ENVIRONMENTS:
            raise ValueError("APP_DEBUG must be false in staging and production")
        return self

    @property
    def api_docs_enabled(self) -> bool:
        """Interactive API documentation is served only locally (ARCHITECTURE section 4)."""
        return self.app_env in ("development", "test")


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once."""
    return Settings()

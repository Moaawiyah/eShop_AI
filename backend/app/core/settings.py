"""Typed application settings from environment variables (NFR-PORT-002).

Every value has a safe local default and is documented in the repository's
`.env.example`. A repository-root `.env` file is read when it exists; real
environment variables take precedence over it.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPOSITORY_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
SHARED_ENVIRONMENTS = frozenset({"staging", "production"})

Environment = Literal["development", "test", "staging", "production"]


def _is_bare_origin(origin: str) -> bool:
    """True for `http(s)://host[:port]` without credentials, path, query or fragment."""
    try:
        parts = urlsplit(origin)
        _ = parts.port  # raises ValueError for an invalid port
    except ValueError:
        return False
    return (
        parts.scheme in ("http", "https")
        and bool(parts.hostname)
        and not parts.username
        and not parts.password
        and origin == f"{parts.scheme}://{parts.netloc}"
    )


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
    # Browser origins allowed by CORS and the Origin check (NFR-SEC-009, SHOP-019).
    allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
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

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string; strip blanks and trailing slashes."""
        items = value.split(",") if isinstance(value, str) else value
        if not isinstance(items, list):
            return items
        return [item.strip().rstrip("/") for item in items if str(item).strip()]

    @field_validator("allowed_origins")
    @classmethod
    def _bare_origins(cls, value: list[str]) -> list[str]:
        for origin in value:
            if not _is_bare_origin(origin):
                raise ValueError(
                    "ALLOWED_ORIGINS entries must be bare origins (scheme://host[:port])"
                )
        return value

    @model_validator(mode="after")
    def _https_origins_in_shared_environments(self) -> Settings:
        if self.app_env in SHARED_ENVIRONMENTS and any(
            not origin.startswith("https://") for origin in self.allowed_origins
        ):
            raise ValueError("ALLOWED_ORIGINS must use https in staging and production")
        return self

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

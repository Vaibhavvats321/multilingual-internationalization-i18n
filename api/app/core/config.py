"""Typed application settings loaded from the environment.

Design rules (PROJECT_SPEC.md section 12):

* Settings are validated once at startup; invalid or missing production
  secrets raise immediately instead of failing at first use.
* Secret values are wrapped in ``SecretStr`` so they cannot leak into logs or
  ``repr()`` output by accident.
* Nothing here is ever exposed to the browser. The frontend receives only the
  explicitly public ``NEXT_PUBLIC_*`` variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

AppEnv = Literal["local", "ci", "staging", "production"]
LogLevel = Literal["debug", "info", "warning", "error"]

#: Placeholder used by ``.env.example``. Rejected outside of ``local``/``ci``.
PLACEHOLDER_SESSION_SECRET = "replace-me-with-a-48-byte-random-secret"  # noqa: S105

#: Repository root: ``<root>/api/app/core/config.py`` -> up three levels.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_API_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration for the API service."""

    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = "local"
    api_base_url: str = "http://localhost:8000"
    web_base_url: str = "http://localhost:3000"

    database_url: SecretStr | None = None

    session_secret: SecretStr = SecretStr(PLACEHOLDER_SESSION_SECRET)
    session_max_age_seconds: int = Field(default=60 * 60 * 12, ge=60, le=60 * 60 * 24 * 30)

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    log_level: LogLevel = "info"

    translation_provider: str = "none"
    translation_api_key: SecretStr | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma separated string for ``CORS_ORIGINS``."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("api_base_url", "web_base_url")
    @classmethod
    def _require_absolute_http_url(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("must be an absolute http(s) URL")
        return value.rstrip("/")

    @model_validator(mode="after")
    def _validate_runtime_rules(self) -> Self:
        if "*" in self.cors_origins:
            raise ValueError(
                "CORS_ORIGINS must not contain '*': credentialed requests require explicit origins"
            )
        if self.translation_provider != "none" and self.translation_api_key is None:
            raise ValueError(
                "TRANSLATION_API_KEY is required when TRANSLATION_PROVIDER is not 'none'"
            )
        if self.app_env in {"staging", "production"}:
            if self.session_secret.get_secret_value() == PLACEHOLDER_SESSION_SECRET:
                raise ValueError(
                    "SESSION_SECRET must be set to a unique secret outside local/ci environments"
                )
            if self.database_url is None:
                raise ValueError("DATABASE_URL is required outside local/ci environments")
        return self

    @property
    def is_production_like(self) -> bool:
        return self.app_env in {"staging", "production"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()

"""Centralised configuration via pydantic-settings.

All environment variables are validated at startup.
Secrets must never be hardcoded — use .env (local) or env vars (prod).
"""

from __future__ import annotations

from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ECHO CHAMBER configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # ── Core ──────────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production", "test"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cortex_port: int = 8000

    # ── Database ───────────────────────────────────────────────────────
    db_user: str = "echo"
    db_password: SecretStr  # required — no default
    db_name: str = "echo_chamber"
    db_host: str = "localhost"
    db_port: int = 5432
    redis_url: str = "redis://localhost:6379/0"

    # ── LLM Providers ──────────────────────────────────────────────────
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    # ── Platform APIs ──────────────────────────────────────────────────
    reddit_client_id: str | None = None
    reddit_client_secret: SecretStr | None = None
    reddit_user_agent: str = "echo-chamber/0.1.0"
    discord_bot_token: SecretStr | None = None
    discord_commander_guild_id: int | None = None

    # ── Optional ───────────────────────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_api_key: SecretStr | None = None
    langchain_project: str = "echo-chamber"
    proxy_provider_url: str | None = None
    proxy_api_key: SecretStr | None = None
    vault_encryption_key: SecretStr | None = None

    @field_validator("db_password", mode="before")
    @classmethod
    def _ensure_db_password_is_secret(cls, v: str | SecretStr | None) -> SecretStr | None:
        """Ensure db_password is never stored as plaintext."""
        if v is None:
            msg = "DB_PASSWORD is required — set it in .env or environment"
            raise ValueError(msg)
        if isinstance(v, SecretStr):
            return v
        return SecretStr(v)

    @model_validator(mode="after")
    def _require_at_least_one_llm_provider(self) -> Settings:
        if not self.openai_api_key and not self.anthropic_api_key:
            msg = (
                "At least one LLM provider must be configured: "
                "set OPENAI_API_KEY or ANTHROPIC_API_KEY"
            )
            raise ValueError(msg)
        return self

    @property
    def database_url(self) -> str:
        """Build database URL from individual components (no secret in memory)."""
        return (
            f"postgresql+asyncpg://"
            f"{self.db_user}:{self.db_password.get_secret_value()}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment in ("development", "test")


# Module-level singleton — import this everywhere
settings = Settings()

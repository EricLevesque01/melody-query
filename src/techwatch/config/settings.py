"""Application configuration loaded from env vars and config files."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_config_dir() -> Path:
    """Return platform-appropriate config directory."""
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(
            __import__("os").environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        )
    return base / "techwatch"


class SmtpSettings(BaseSettings):
    """SMTP configuration for email delivery."""

    model_config = SettingsConfigDict(env_prefix="SMTP_")

    host: str = "localhost"
    port: int = 587
    username: Optional[str] = None
    password: Optional[SecretStr] = None
    use_tls: bool = True


class Settings(BaseSettings):
    """Top-level application settings.

    Values are resolved in order: env vars → .env file → defaults.
    """

    model_config = SettingsConfigDict(
        env_prefix="TECHWATCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── API keys ────────────────────────────────────────────
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        alias="OPENAI_API_KEY",
    )
    bestbuy_api_key: SecretStr = Field(
        default=SecretStr(""),
        alias="BESTBUY_API_KEY",
    )
    ebay_client_id: SecretStr = Field(
        default=SecretStr(""),
        alias="EBAY_CLIENT_ID",
    )
    ebay_client_secret: SecretStr = Field(
        default=SecretStr(""),
        alias="EBAY_CLIENT_SECRET",
    )

    # ── Email ───────────────────────────────────────────────
    email_from: str = "techwatch@localhost"
    smtp: SmtpSettings = Field(default_factory=SmtpSettings)

    # ── Database ────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///techwatch.db",
        alias="DATABASE_URL",
    )

    # ── Defaults ────────────────────────────────────────────
    country: str = "US"
    currency: str = "USD"
    locale: str = "en_US"
    timezone: str = "America/New_York"

    # ── Mock / demo mode ────────────────────────────────────
    mock: bool = False  # Set TECHWATCH_MOCK=true for demo mode

    # ── Paths ───────────────────────────────────────────────
    config_dir: Path = Field(default_factory=_default_config_dir)
    cache_dir: Optional[Path] = None

    # ── LLM ─────────────────────────────────────────────────
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.1

    # ── Adapter defaults ────────────────────────────────────
    default_cache_ttl: int = 300  # seconds
    default_max_qps: float = 5.0
    default_timeout: float = 30.0
    default_max_retries: int = 3

    def get_cache_dir(self) -> Path:
        """Return the resolved cache directory, creating it if needed."""
        d = self.cache_dir or (self.config_dir / "cache")
        d.mkdir(parents=True, exist_ok=True)
        return d


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the singleton settings instance."""
    global _settings  # noqa: PLW0603
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings


def reset_settings() -> None:
    """Reset the singleton (useful in tests)."""
    global _settings  # noqa: PLW0603
    _settings = None

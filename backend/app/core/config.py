"""Application settings, loaded from environment variables (and `.env`)."""
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "MarketMapper"
    environment: str = "development"

    # Infrastructure
    database_url: str = "postgresql+psycopg://marketmapper:marketmapper@localhost:5432/marketmapper"
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "research"
    run_jobs_inline: bool = False  # process uploads synchronously (tests / no Redis)

    # Auth
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 60 * 12
    allow_signup: bool = True

    # Research — AI provider ("auto" uses whichever key is set, Anthropic first)
    ai_provider: str = "auto"
    anthropic_api_key: str = ""
    agent_model: str = "claude-sonnet-5-5"
    openai_api_key: str = ""
    openai_model: str = "gpt-6.2-sol"
    max_pages_per_site: int = 4
    request_timeout_seconds: int = 15
    allow_private_urls: bool = False  # only for local testing against localhost sites
    offers_path: Path = BACKEND_DIR / "offers.yaml"

    # Uploads
    max_upload_mb: int = 10
    max_rows_per_upload: int = 2000

    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def resolved_ai_provider(self) -> str | None:
        """'anthropic', 'openai', or None (rule-based analysis)."""
        keys = {"anthropic": self.anthropic_api_key, "openai": self.openai_api_key}
        if self.ai_provider in keys:
            return self.ai_provider if keys[self.ai_provider] else None
        return next((name for name, key in keys.items() if key), None)

    @property
    def ai_enabled(self) -> bool:
        return self.resolved_ai_provider is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()

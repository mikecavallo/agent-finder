"""Application settings, loaded from environment variables (and an optional .env file)."""

import logging
import secrets
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/agent_finder.db"

    # Auth. When SECRET_KEY is unset a random key is generated per process,
    # which means tokens stop working after a restart. Set it in real deployments.
    secret_key: str = ""
    access_token_expire_minutes: int = 60 * 12

    # LLM provider selection. If the chosen provider has no API key configured,
    # the app falls back to the deterministic mock scorer and reports that via /api/health.
    llm_provider: Literal["anthropic", "openai", "mock"] = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    anthropic_effort: Literal["low", "medium", "high"] = "medium"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    llm_concurrency: int = 4

    # Demo mode seeds a demo account, a sample opening and fictional resumes on startup.
    demo_mode: bool = False
    demo_username: str = "demo"
    demo_password: str = "demo-password"

    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_mb: int = 5
    max_files_per_upload: int = 20

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.secret_key:
        logger.warning("SECRET_KEY is not set; generating an ephemeral key for this process.")
        settings.secret_key = secrets.token_urlsafe(48)
    return settings

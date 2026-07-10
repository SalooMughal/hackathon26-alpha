from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Required vars without defaults (DATABASE_URL, OPENAI_API_KEY) cause a
    loud validation error at startup if missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    OPENAI_API_KEY: str

    PLANNER_MODEL: str = "gpt-4o-mini"
    SUMMARIZER_MODEL: str = "gpt-4o"
    VALIDATOR_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30
    MAX_REVISIONS: int = 2

    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    @field_validator("DATABASE_URL")
    @classmethod
    def _require_asyncpg_driver(cls, v: str) -> str:
        if v.startswith("postgresql+asyncpg://") and "sslmode=" in v:
            raise ValueError(
                "asyncpg does not accept 'sslmode' in the URL; "
                "SSL is configured via connect_args in app/db/session.py"
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

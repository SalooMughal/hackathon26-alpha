from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db.connect import normalize_database_url


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    OPENAI_API_KEY: str

    SANITIZER_MODEL: str = "gpt-4o-mini"
    PLANNER_MODEL: str = "gpt-4o-mini"
    SUMMARIZER_MODEL: str = "gpt-4o"
    VALIDATOR_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 2
    MAX_REVISIONS: int = 2
    GRAPH_RECURSION_LIMIT: int = 15

    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    CORS_ORIGINS: str = Field(default="http://localhost:5173")

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        return normalize_database_url(v)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

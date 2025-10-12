from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/priceoptim",
        description="Primary Postgres connection string (async)",
    )
    SQLITE_URL: str = Field(
        default="sqlite+aiosqlite:///./priceoptim.db",
        description="Fallback SQLite connection string (async)",
    )

    # LLM provider (optional)
    OLLAMA_HOST: str = Field(
        default="http://localhost:11434",
        description="Ollama server host URL"
    )
    OLLAMA_MODEL: str = Field(
        default="gemma3:4b",
        description="Ollama model to use for pricing insights"
    )

    # ML Matching
    USE_ML_MATCHING: bool = Field(
        default=True,
        description="Enable ML-based product matching using sentence transformers",
    )
    ML_MODEL_NAME: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model to use for embeddings",
    )

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = Field(default_factory=list)

    # Scraping is always enabled in this build

    # Misc
    APP_NAME: str = "Price Optim AI API"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

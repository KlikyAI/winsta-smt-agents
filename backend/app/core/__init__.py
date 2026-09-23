"""Core configuration module using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_name: str = "prompt-trends-automation"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/prompt_trends"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/prompt_trends"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 10080  # 7 days

    # AI Provider
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o"
    ai_fallback_provider: Optional[str] = None
    ai_fallback_model: Optional[str] = None
    ai_api_key: Optional[str] = None

    # Platform API Keys
    instagram_access_token: Optional[str] = None
    tiktok_access_token: Optional[str] = None
    youtube_api_key: Optional[str] = None
    x_api_key: Optional[str] = None
    x_api_secret: Optional[str] = None
    google_trends_api_key: Optional[str] = None

    # Integration Endpoints
    sarah_agent_base_url: Optional[str] = None
    sarah_agent_api_key: Optional[str] = None
    social_media_agent_base_url: Optional[str] = None
    social_media_agent_api_key: Optional[str] = None

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Scoring
    scoring_threshold: float = 70.0

    # Trend Discovery
    default_limit_per_source: int = 100
    discovery_schedule_minutes: int = 60

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

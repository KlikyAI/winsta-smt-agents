"""Core configuration module using Pydantic Settings."""

from functools import lru_cache
import logging
import os
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# httpx logs full request URLs at INFO, which can expose OAuth query tokens
# (for example provider ``access_token`` parameters) in worker logs. Keep
# third-party transport logs quiet; application events remain structured and
# intentionally record only safe identifiers/statuses.
for _logger_name in ("httpx", "httpcore"):
    logging.getLogger(_logger_name).setLevel(logging.WARNING)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Production containers receive secrets through Docker's ``env_file``
        # mechanism.  Do not make the non-root runtime user read the host
        # .env file (which is intentionally mode 600).  Local development
        # still loads .env as before.
        env_file=None if os.getenv("APP_ENV", "").lower() == "production" else ".env",
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
    # Optional direct/session-mode URL reserved for Alembic migrations.
    direct_url: Optional[str] = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_minutes: int = 10080  # 7 days

    # Multi-Provider AI / LLM Configuration
    ai_provider: str = "deepseek"  # deepseek | openai | anthropic | gemini | groq | ollama | openrouter | mistral | litellm
    ai_model: str = "deepseek-chat"
    ai_fallback_provider: Optional[str] = "openai"
    ai_fallback_model: Optional[str] = "gpt-4o-mini"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 2048
    ai_timeout_seconds: int = 60

    # Generic AI API Key (used as fallback for ai_provider)
    # Secrets must come from the environment/secret manager only. Never ship
    # a provider key as a source-code default.
    ai_api_key: Optional[str] = None

    # Provider-Specific API Keys & Custom Endpoints
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = "https://api.openai.com/v1"

    # Cloudflare Workers AI (image previews)
    cloudflare_account_id: Optional[str] = None
    cloudflare_api_token: Optional[str] = None
    cloudflare_flux_model: str = "@cf/black-forest-labs/flux-1-schnell"
    cloudflare_flux_steps: int = 4

    anthropic_api_key: Optional[str] = None
    anthropic_api_base: Optional[str] = "https://api.anthropic.com/v1"

    gemini_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    deepseek_api_key: Optional[str] = None
    deepseek_api_base: Optional[str] = "https://api.deepseek.com"

    groq_api_key: Optional[str] = None
    groq_api_base: Optional[str] = "https://api.groq.com/openai/v1"

    openrouter_api_key: Optional[str] = None
    openrouter_api_base: Optional[str] = "https://openrouter.ai/api/v1"

    mistral_api_key: Optional[str] = None
    mistral_api_base: Optional[str] = "https://api.mistral.ai/v1"

    ollama_base_url: Optional[str] = "http://localhost:11434"

    # OAuth 2.0 & Platform API Credentials
    # Meta (Instagram Graph API)
    meta_client_id: Optional[str] = None
    meta_client_secret: Optional[str] = None
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_login_config_id: Optional[str] = None
    instagram_app_id: Optional[str] = None
    instagram_app_secret: Optional[str] = None
    instagram_webhook_verify_token: Optional[str] = None
    instagram_access_token: Optional[str] = None  # Fallback static token

    # Threads API (separate Meta Threads app credentials)
    threads_app_id: Optional[str] = None
    threads_app_secret: Optional[str] = None

    # TikTok for Developers / Research API
    tiktok_environment: str = "production"
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    tiktok_sandbox_client_key: Optional[str] = None
    tiktok_sandbox_client_secret: Optional[str] = None
    tiktok_oauth_scopes: Optional[str] = None
    tiktok_access_token: Optional[str] = None  # Fallback static token
    # TikTok restricts unaudited clients to private visibility. Keep this
    # false until the Content Posting API audit has been approved.
    tiktok_client_audited: bool = False

    # X (Twitter API v2)
    x_client_id: Optional[str] = None
    x_client_secret: Optional[str] = None
    x_api_key: Optional[str] = None
    x_api_secret: Optional[str] = None
    x_bearer_token: Optional[str] = None  # Fallback static token

    # Google
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    youtube_api_key: Optional[str] = None
    google_trends_api_key: Optional[str] = None

    # LinkedIn
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_oauth_scopes: Optional[str] = None
    linkedin_api_version: str = "202608"

    # Supabase Storage (server-side only; never expose the secret key to the browser)
    supabase_url: Optional[str] = None
    supabase_secret_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    supabase_storage_bucket: str = "social-media-assets"
    supabase_trend_reference_bucket: str = "trend-reference-images"
    supabase_signed_url_ttl_seconds: int = 604800

    # Public backend base URL registered for provider OAuth callbacks.
    social_oauth_callback_base_url: str = "http://localhost:8000"
    social_token_encryption_key: Optional[str] = None
    social_frontend_base_url: str = "http://localhost:3001"
    meta_graph_api_version: str = "v25.0"

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
    discovery_schedule_enabled: bool = True
    discovery_schedule_minutes: int = 60
    discovery_schedule_country: str = "ID"
    discovery_schedule_category: str = "beauty_skincare"
    discovery_schedule_aesthetic: str = "minimalist_organic"
    discovery_schedule_time_window: str = "24h"
    discovery_schedule_sources: str = "google_trends,tiktok,instagram,youtube,x,linkedin"

    # Proxy Rotation & Anti-Rate-Limit Pool for Scrapers
    proxy_rotation_enabled: bool = True
    proxy_list: str = ""
    proxy_timeout_seconds: float = 12.0
    proxy_max_retries: int = 3
    proxy_backoff_factor: float = 1.5

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def tiktok_client_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Return credentials for the selected TikTok environment."""
        if self.tiktok_environment.strip().lower() == "sandbox":
            return self.tiktok_sandbox_client_key, self.tiktok_sandbox_client_secret
        return self.tiktok_client_key, self.tiktok_client_secret

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Fail fast instead of starting production with a known JWT key."""
        if self.is_production and self.jwt_secret in {"", "change-me-in-production"}:
            raise ValueError("JWT_SECRET must be explicitly configured in production")
        return self


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

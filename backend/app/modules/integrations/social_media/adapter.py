"""Social Media Agent integration adapter (stubbed)."""

import httpx
import structlog

from app.core.config import get_settings
from app.modules.integrations.contracts import (
    IntegrationAdapterContract,
    IntegrationPayload,
    IntegrationResult,
)

logger = structlog.get_logger()


class SocialMediaAgentAdapter(IntegrationAdapterContract):
    """Adapter for delivering approved trends to Social Media AI Agent."""

    @property
    def integration_name(self) -> str:
        return "social_media_agent"

    async def deliver(self, payload: IntegrationPayload) -> IntegrationResult:
        settings = get_settings()
        if not settings.social_media_agent_base_url:
            logger.warning("social_media_agent_not_configured")
            return IntegrationResult(
                success=False,
                error="Social Media Agent base URL not configured",
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.social_media_agent_base_url}/api/v1/trends/ingest",
                    json={
                        "trend_id": payload.trend_id,
                        "prompt_package_id": payload.prompt_package_id,
                        "score": payload.score,
                        "approved_at": payload.approved_at,
                        "source": payload.source,
                        "data": payload.data,
                    },
                    headers={
                        "X-Api-Key": settings.social_media_agent_api_key or "",
                        "Content-Type": "application/json",
                    },
                )
                return IntegrationResult(
                    success=response.is_success,
                    status_code=response.status_code,
                    response_body=response.json() if response.is_success else None,
                    error=(f"Upstream integration returned HTTP {response.status_code}" if not response.is_success else None),
                )
        except Exception as e:
            logger.error("social_media_agent_delivery_failed", error=str(e))
            return IntegrationResult(success=False, error=f"Integration request failed: {type(e).__name__}")

    async def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.social_media_agent_base_url)

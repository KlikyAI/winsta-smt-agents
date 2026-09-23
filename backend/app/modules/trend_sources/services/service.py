"""Trend Sources module — service."""

import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from app.core.exceptions import NotFoundException
from app.modules.trend_sources.models import TrendSource
from app.modules.trend_sources.repositories import TrendSourceRepository
from app.modules.trend_sources.schemas import (
    TrendSourceDetailResponse,
    TrendSourceResponse,
    UpdateTrendSourceRequest,
)


# Sensitive keys to strip from configuration in responses
_SENSITIVE_KEY_PARTS = (
    "access_token",
    "refresh_token",
    "api_key",
    "api_secret",
    "client_secret",
    "bearer_token",
    "password",
    "secret",
    "token",
    "private_key",
)


def _strip_sensitive(config: dict[str, Any] | None) -> dict[str, Any] | None:
    """Remove sensitive fields recursively from configuration responses."""
    if not config:
        return config

    def sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                normalized = str(key).lower().replace("-", "_")
                if any(part in normalized for part in _SENSITIVE_KEY_PARTS):
                    result[key] = "***"
                else:
                    result[key] = sanitize(item)
            return result
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        return value

    return sanitize(config)


class TrendSourceService:
    def __init__(self, repo: TrendSourceRepository) -> None:
        self.repo = repo

    async def get_all(self) -> list[TrendSourceResponse]:
        sources = await self.repo.get_all(limit=200)
        responses = []
        for source in sources:
            response = TrendSourceResponse.model_validate(source)
            response.configuration = _strip_sensitive(source.configuration)
            responses.append(response)
        return responses

    async def get_by_id(self, source_id: uuid.UUID) -> TrendSourceDetailResponse:
        source = await self.repo.get_by_id(source_id)
        if not source:
            raise NotFoundException(message="Trend source not found")
        resp = TrendSourceDetailResponse.model_validate(source)
        resp.configuration = _strip_sensitive(source.configuration)
        return resp

    async def update(self, source_id: uuid.UUID, data: UpdateTrendSourceRequest) -> TrendSourceResponse:
        update_data = data.model_dump(exclude_unset=True)
        source = await self.repo.update(source_id, update_data)
        if not source:
            raise NotFoundException(message="Trend source not found")
        resp = TrendSourceResponse.model_validate(source)
        resp.configuration = _strip_sensitive(source.configuration)
        return resp

    async def enable(self, source_id: uuid.UUID) -> TrendSourceResponse:
        source = await self.repo.update(source_id, {"enabled": True})
        if not source:
            raise NotFoundException(message="Trend source not found")
        resp = TrendSourceResponse.model_validate(source)
        resp.configuration = _strip_sensitive(source.configuration)
        return resp

    async def disable(self, source_id: uuid.UUID) -> TrendSourceResponse:
        source = await self.repo.update(source_id, {"enabled": False})
        if not source:
            raise NotFoundException(message="Trend source not found")
        resp = TrendSourceResponse.model_validate(source)
        resp.configuration = _strip_sensitive(source.configuration)
        return resp

    async def get_enabled_sources(self) -> Sequence[TrendSource]:
        return await self.repo.get_enabled_sources()

"""Prompt Generation module — service."""

import uuid
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

from app.core.exceptions import NotFoundException, ValidationException
from app.modules.ai.services.image_generation import GeneratedImage, image_generation_service
from app.modules.prompt_generation.repositories import PromptPackageRepository
from app.modules.prompt_generation.schemas import (
    PromptPackageResponse,
    PublicPromptPage,
    PublicPromptResponse,
)
from app.modules.prompt_generation.services.reference_images import trend_reference_image_service


class PromptGenerationService:
    def __init__(self, repo: PromptPackageRepository) -> None:
        self.repo = repo

    async def get_packages(self, trend_id: uuid.UUID) -> list[PromptPackageResponse]:
        packages = await self.repo.get_by_trend(trend_id)
        return [PromptPackageResponse.model_validate(p) for p in packages]

    async def get_latest(self, trend_id: uuid.UUID) -> PromptPackageResponse:
        package = await self.repo.get_latest(trend_id)
        if not package:
            raise NotFoundException(message="No prompt packages found for this trend")
        return PromptPackageResponse.model_validate(package)

    async def generate_reference_preview(
        self,
        *,
        prompt_package_id: uuid.UUID,
        prompt: str,
        aspect_ratio: str,
        model: str,
    ) -> GeneratedImage:
        package = await self.repo.get_by_id(prompt_package_id)
        if not package:
            raise NotFoundException(message="Prompt package not found")

        generated = await image_generation_service.generate(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            model=model,
        )
        public_url = await trend_reference_image_service.store(
            trend_id=package.trend_id,
            prompt_package_id=package.id,
            generated=generated,
        )
        package.trend_reference_image_url = public_url
        await self.repo.session.commit()
        return replace(
            generated,
            image_url=public_url,
            trend_reference_image_url=public_url,
            image_bytes=None,
        )

    async def list_public(
        self,
        *,
        page: int,
        page_size: int,
        date_from: date | None,
        date_to: date | None,
        category: str | None,
        search: str | None,
        has_reference_image: bool | None,
        min_quality_score: float | None,
        generation_mode: str | None,
        latest_only: bool,
        sort: Literal["newest", "oldest", "quality_desc"],
    ) -> PublicPromptPage:
        if date_from and date_to and date_from > date_to:
            raise ValidationException(message="date_from must be on or before date_to")
        start = datetime.combine(date_from, time.min, tzinfo=timezone.utc) if date_from else None
        end = (
            datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
            if date_to
            else None
        )
        packages, total = await self.repo.list_public(
            page=page,
            page_size=page_size,
            date_from=start,
            date_to_exclusive=end,
            category=category,
            search=search,
            has_reference_image=has_reference_image,
            min_quality_score=min_quality_score,
            generation_mode=generation_mode,
            latest_only=latest_only,
            sort=sort,
        )
        return PublicPromptPage(
            items=[PublicPromptResponse.model_validate(package) for package in packages],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

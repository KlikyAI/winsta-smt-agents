"""Prompt Generation module — dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.prompt_generation.repositories import PromptPackageRepository
from app.modules.prompt_generation.services import PromptGenerationService


async def get_prompt_package_repository(db: AsyncSession = Depends(get_db)) -> PromptPackageRepository:
    return PromptPackageRepository(db)


async def get_prompt_generation_service(
    repo: PromptPackageRepository = Depends(get_prompt_package_repository),
) -> PromptGenerationService:
    return PromptGenerationService(repo)

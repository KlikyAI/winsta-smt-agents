import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundException
from app.modules.social_media.services.service import SocialMediaService


def _service(organization_id: uuid.UUID | None) -> SocialMediaService:
    return SocialMediaService(
        organization_repo=MagicMock(),
        connection_repo=MagicMock(),
        brief_repo=MagicMock(),
        content_repo=MagicMock(),
        publish_job_repo=MagicMock(),
        organization_id=organization_id,
    )


@pytest.mark.asyncio
async def test_authenticated_social_service_resolves_selected_workspace() -> None:
    organization_id = uuid.uuid4()
    organization = SimpleNamespace(id=organization_id, status="active")
    service = _service(organization_id)
    service.organization_repo.get_by_id = AsyncMock(return_value=organization)
    service.organization_repo.get_by_slug = AsyncMock()

    resolved = await service._get_default_organization()

    assert resolved is organization
    service.organization_repo.get_by_id.assert_awaited_once_with(organization_id)
    service.organization_repo.get_by_slug.assert_not_awaited()


@pytest.mark.asyncio
async def test_selected_workspace_must_be_active() -> None:
    service = _service(uuid.uuid4())
    service.organization_repo.get_by_id = AsyncMock(
        return_value=SimpleNamespace(status="suspended")
    )

    with pytest.raises(NotFoundException, match="Active workspace"):
        await service._get_default_organization()

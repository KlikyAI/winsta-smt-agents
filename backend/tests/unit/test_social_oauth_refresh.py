"""Unit tests for OAuth Token Auto-Refresh Daemon."""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.social_media.models import SocialCredential
from app.modules.social_media.providers.meta import MetaGraphClient
from app.modules.social_media.providers.oauth import OAuthToken
from app.modules.social_media.security import encrypt_secret, decrypt_secret
from app.workers.social_tasks import _refresh_expiring_social_tokens


@pytest.mark.asyncio
async def test_meta_graph_client_refresh_long_lived_token():
    client = MetaGraphClient()
    client.settings.meta_app_id = "test_app_id"
    client.settings.meta_app_secret = "test_app_secret"

    mock_payload = {
        "access_token": "new_long_lived_token_123",
        "token_type": "bearer",
        "expires_in": 5184000,
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.json = lambda: mock_payload
        mock_get.return_value = mock_response

        result = await client.refresh_long_lived_token("old_token_xyz")
        assert result["access_token"] == "new_long_lived_token_123"
        assert result["expires_at"] is not None


@pytest.mark.asyncio
async def test_refresh_expiring_social_tokens_process():
    org_id = uuid.uuid4()
    expiring_at = datetime.now(timezone.utc) + timedelta(hours=2)

    meta_cred = SocialCredential(
        organization_id=org_id,
        provider="meta",
        credential_type="oauth2",
        encrypted_access_token=encrypt_secret("old_meta_token"),
        expires_at=expiring_at,
        status="active",
    )

    x_cred = SocialCredential(
        organization_id=org_id,
        provider="x",
        credential_type="oauth2",
        encrypted_access_token=encrypt_secret("old_x_access"),
        encrypted_refresh_token=encrypt_secret("valid_x_refresh"),
        expires_at=expiring_at,
        scopes=["tweet.read", "tweet.write"],
        status="active",
    )

    mock_db_result = MagicMock()
    mock_db_result.scalars.return_value.all.return_value = [meta_cred, x_cred]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_db_result

    with patch("app.workers.social_tasks.get_celery_task_session") as mock_get_session:
        mock_get_session.return_value.__aenter__.return_value = mock_session
        mock_get_session.return_value.__aexit__.return_value = None

        with patch.object(
            MetaGraphClient,
            "refresh_long_lived_token",
            new_callable=AsyncMock,
            return_value={"access_token": "refreshed_meta_token", "expires_at": datetime.now(timezone.utc) + timedelta(days=60)},
        ):
            with patch("app.workers.social_tasks.get_oauth_client") as mock_get_client:
                mock_oauth_client = AsyncMock()
                mock_oauth_client.refresh_token.return_value = OAuthToken(
                    access_token="refreshed_x_access",
                    refresh_token="new_x_refresh",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
                    scopes=["tweet.read", "tweet.write"],
                    raw={},
                )
                mock_get_client.return_value = mock_oauth_client

                summary = await _refresh_expiring_social_tokens()

                assert summary["status"] == "completed"
                assert summary["checked_count"] == 2
                assert summary["refreshed_count"] == 2
                assert summary["failed_count"] == 0

                assert decrypt_secret(meta_cred.encrypted_access_token) == "refreshed_meta_token"
                assert decrypt_secret(x_cred.encrypted_access_token) == "refreshed_x_access"
                assert decrypt_secret(x_cred.encrypted_refresh_token) == "new_x_refresh"

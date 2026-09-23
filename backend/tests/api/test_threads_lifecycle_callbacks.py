"""Tests for public Threads lifecycle callback URLs."""

import pytest


@pytest.mark.asyncio
async def test_threads_uninstall_callback_is_reachable(client) -> None:
    response = await client.post(
        "/api/v1/social/webhooks/threads/uninstall",
        content=b"signed_request=placeholder",
    )

    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_threads_remove_callback_returns_deletion_instructions(client) -> None:
    response = await client.post(
        "/api/v1/social/webhooks/threads/remove",
        content=b"signed_request=placeholder",
    )

    assert response.status_code == 200
    assert response.json()["url"] == "https://bookmind.my.id/data-deletion"
    assert response.json()["confirmation_code"]

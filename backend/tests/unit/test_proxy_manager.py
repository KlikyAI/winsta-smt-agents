"""Unit tests for ProxyPoolManager and anti-bot retry mechanisms."""

import pytest
import httpx
from app.core.proxy_manager import ProxyPoolManager, USER_AGENTS


def test_proxy_manager_initializes_and_parses_list():
    manager = ProxyPoolManager()
    manager._proxies = ["http://proxy1:8080", "http://proxy2:8080", "http://proxy3:8080"]
    manager._failing_proxies.clear()

    assert manager.has_proxies is True
    first = manager.get_next_proxy()
    second = manager.get_next_proxy()
    third = manager.get_next_proxy()
    fourth = manager.get_next_proxy()

    assert first == "http://proxy1:8080"
    assert second == "http://proxy2:8080"
    assert third == "http://proxy3:8080"
    assert fourth == "http://proxy1:8080"


def test_proxy_manager_handles_failure_and_cooldown():
    manager = ProxyPoolManager()
    manager._proxies = ["http://proxy1:8080", "http://proxy2:8080"]
    manager._failing_proxies.clear()

    # Report failure on proxy1
    manager.report_proxy_failure("http://proxy1:8080", reason="ConnectTimeout")
    assert "http://proxy1:8080" in manager._failing_proxies

    # Next proxy should skip proxy1 and return proxy2
    next_p = manager.get_next_proxy()
    assert next_p == "http://proxy2:8080"


def test_proxy_manager_headers_and_user_agent_rotation():
    manager = ProxyPoolManager()
    headers = manager.get_default_headers({"X-Custom": "test"})

    assert "User-Agent" in headers
    assert headers["User-Agent"] in USER_AGENTS
    assert headers["X-Custom"] == "test"
    assert "Sec-Ch-Ua" in headers


@pytest.mark.asyncio
async def test_proxy_manager_client_creation():
    manager = ProxyPoolManager()
    client = manager.create_client(timeout=5.0, force_direct=True)
    try:
        assert isinstance(client, httpx.AsyncClient)
        assert client.timeout.read == 5.0
    finally:
        await client.aclose()

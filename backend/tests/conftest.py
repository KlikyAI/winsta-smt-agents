import os

# Ensure test encryption key for social token security in test environments
os.environ.setdefault(
    "SOCIAL_TOKEN_ENCRYPTION_KEY",
    "-PysoH1OfHr3SrrwwHgVQ9Ed8JeZ0zguSGdTRqh_XTo=",
)

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for API testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_trend_run_request() -> dict:
    return {
        "sources": ["instagram", "tiktok"],
        "categories": ["ai_visual"],
        "market": "global",
        "language": "en",
        "limit_per_source": 50,
    }


@pytest.fixture
def sample_scoring_weights() -> list[dict]:
    return [
        {"signal_type": "freshness", "weight": 20.0},
        {"signal_type": "velocity", "weight": 20.0},
        {"signal_type": "engagement_quality", "weight": 15.0},
        {"signal_type": "winsta_relevance", "weight": 20.0},
        {"signal_type": "visual_generatability", "weight": 15.0},
        {"signal_type": "novelty", "weight": 10.0},
    ]

"""Regression coverage for JSON-safe request validation responses."""

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, field_validator
import pytest

from app.core.exceptions import register_exception_handlers


class EnglishPayload(BaseModel):
    language: str

    @field_validator("language")
    @classmethod
    def english_only(cls, value: str) -> str:
        if value != "en":
            raise ValueError("English only")
        return value


@pytest.mark.asyncio
async def test_value_error_context_is_json_serializable() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/validate")
    async def validate(payload: EnglishPayload):
        return payload

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/validate", json={"language": "id"})

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert response.json()["errors"][0]["ctx"]["error"] == "English only"

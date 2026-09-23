"""AI Module — API router.

Endpoints to query configured LLM providers, model catalogs,
test real-time LLM completions, and generate live AI visual previews.
"""

import json
import uuid
from typing import Optional
import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.responses import success_response
from app.core.rate_limit import rate_limit
from app.modules.ai.services.service import ai_service
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.prompt_generation.dependencies import get_prompt_generation_service
from app.modules.prompt_generation.services import PromptGenerationService

logger = structlog.get_logger()
router = APIRouter(prefix="/ai", tags=["AI & LLM Engine"])


class AITestRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to test with LLM")
    provider: Optional[str] = Field(None, description="Target provider (e.g. openai, anthropic, gemini, deepseek, groq, ollama)")
    model: Optional[str] = Field(None, description="Target model ID")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1000, ge=1, le=4096)


class ImageGenerationRequest(BaseModel):
    prompt_package_id: uuid.UUID = Field(..., description="Prompt package that owns the persisted preview")
    prompt: str = Field(..., min_length=1, description="Text prompt for image synthesis")
    aspect_ratio: Optional[str] = Field("16:9", description="1:1 | 16:9 | 9:16 | 4:5")
    model: Optional[str] = Field(
        "cloudflare-flux",
        description="cloudflare-flux | flux-realism | dall-e-3",
    )


class AISettingsUpdateRequest(BaseModel):
    ai_provider: Optional[str] = Field(None, description="Active primary provider (e.g. deepseek, openai, anthropic, gemini, groq)")
    ai_model: Optional[str] = Field(None, description="Active model ID (e.g. deepseek-chat, gpt-4o, claude-3-5-sonnet-20241022)")
    ai_fallback_provider: Optional[str] = Field(None, description="Fallback provider")
    ai_fallback_model: Optional[str] = Field(None, description="Fallback model")
    ai_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    ai_max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    # Optional dynamic API keys
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None


@router.get("/settings", response_model=None)
async def get_ai_settings(
    _user=Depends(get_current_user),
):
    """Fetch current dynamic AI settings (active model, provider, fallback)."""
    settings = await ai_service.get_runtime_settings()
    return success_response(data=settings)


@router.put("/settings", response_model=None)
async def update_ai_settings(
    body: AISettingsUpdateRequest,
    _user=Depends(require_permission("manage:settings")),
):
    """Update dynamic AI settings directly from UI without editing .env."""
    updated = await ai_service.update_runtime_settings(body.model_dump(exclude_unset=True))
    return success_response(data=updated, message="AI runtime settings updated successfully")


@router.get("/providers", response_model=None)
async def list_providers(
    _user=Depends(get_current_user),
):
    """List all supported AI providers, configuration status, and recommended models."""
    statuses = await ai_service.get_provider_statuses()
    return success_response(data=statuses)


@router.post("/generate", response_model=None)
async def test_generate(
    body: AITestRequest,
    _user=Depends(get_current_user),
    _rate_limit=Depends(rate_limit("ai:generate", limit=30, window_seconds=60)),
):
    """Test completion using the selected or default AI provider."""
    resp = await ai_service.generate(
        capability="test_completion",
        prompt=body.prompt,
        provider_name=body.provider,
        model_name=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )
    return success_response(data={
        "content": resp.content,
        "provider": resp.provider,
        "model": resp.model,
        "latency_ms": resp.latency_ms,
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
    })


@router.post("/generate/stream", response_model=None)
async def test_generate_stream(
    body: AITestRequest,
    _user=Depends(get_current_user),
    _rate_limit=Depends(rate_limit("ai:generate_stream", limit=30, window_seconds=60)),
):
    """Stream real-time tokens using Server-Sent Events (SSE)."""
    async def event_generator():
        try:
            async for token in ai_service.generate_stream(
                capability="test_completion_stream",
                prompt=body.prompt,
                provider_name=body.provider,
                model_name=body.model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate-image", response_model=None)
async def generate_image_preview(
    body: ImageGenerationRequest,
    service: PromptGenerationService = Depends(get_prompt_generation_service),
    _user=Depends(get_current_user),
    _rate_limit=Depends(rate_limit("ai:image", limit=10, window_seconds=60)),
):
    """Generate and permanently store a trend reference image preview."""
    prompt = body.prompt.strip()
    aspect = body.aspect_ratio or "16:9"
    result = await service.generate_reference_preview(
        prompt_package_id=body.prompt_package_id,
        prompt=prompt,
        aspect_ratio=aspect,
        model=body.model or "cloudflare-flux",
    )
    return success_response(data=result.model_dump())

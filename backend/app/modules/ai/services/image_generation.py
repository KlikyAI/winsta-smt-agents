"""Reusable image generation service for previews and social media creatives."""

import base64
import random
import time
import urllib.parse
from dataclasses import asdict, dataclass

import httpx
import structlog

from app.core.config import get_settings


logger = structlog.get_logger()


@dataclass(frozen=True)
class GeneratedImage:
    image_url: str
    provider: str
    model: str
    prompt: str
    latency_ms: int
    aspect_ratio: str
    mime_type: str | None = None
    image_bytes: bytes | None = None
    trend_reference_image_url: str | None = None

    def model_dump(self) -> dict:
        payload = asdict(self)
        payload.pop("image_bytes", None)
        return payload


class ImageGenerationService:
    """Generate a public image URL while keeping provider details in one place."""

    DIMENSIONS = {
        "1:1": (1024, 1024),
        "1.91:1": (1280, 670),
        "16:9": (1280, 720),
        "9:16": (720, 1280),
        "4:5": (896, 1120),
    }

    async def generate(
        self,
        *,
        prompt: str,
        aspect_ratio: str,
        model: str = "flux-realism",
    ) -> GeneratedImage:
        settings = get_settings()
        clean_prompt = " ".join(prompt.split())[:4000]
        width, height = self.DIMENSIONS.get(aspect_ratio, self.DIMENSIONS["1:1"])
        started = time.perf_counter()

        if model in {"cloudflare-flux", settings.cloudflare_flux_model}:
            if settings.cloudflare_account_id and settings.cloudflare_api_token:
                try:
                    endpoint = (
                        "https://api.cloudflare.com/client/v4/accounts/"
                        f"{settings.cloudflare_account_id}/ai/run/{settings.cloudflare_flux_model}"
                    )
                    headers = {
                        "Authorization": f"Bearer {settings.cloudflare_api_token}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "prompt": clean_prompt[:2048],
                        "steps": max(1, min(settings.cloudflare_flux_steps, 8)),
                        "seed": random.SystemRandom().randint(1, 2_147_483_647),
                    }
                    async with httpx.AsyncClient(timeout=90.0) as client:
                        response = await client.post(endpoint, json=payload, headers=headers)
                        response.raise_for_status()
                    response_payload = response.json()
                    if response_payload.get("success") is False:
                        raise ValueError("Cloudflare Workers AI returned an unsuccessful response")
                    result = response_payload.get("result", response_payload)
                    encoded_image = result.get("image") if isinstance(result, dict) else None
                    if not encoded_image:
                        raise ValueError("Cloudflare Workers AI returned no image")
                    image_bytes = base64.b64decode(encoded_image, validate=True)
                    return GeneratedImage(
                        image_url="",
                        provider="cloudflare-workers-ai",
                        model=settings.cloudflare_flux_model,
                        prompt=clean_prompt,
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        # FLUX.1 schnell exposes prompt/steps only and returns a square image.
                        aspect_ratio="1:1",
                        mime_type="image/jpeg",
                        image_bytes=image_bytes,
                    )
                except Exception as exc:
                    logger.warning(
                        "image_provider_fallback",
                        provider="cloudflare-workers-ai",
                        error=str(exc),
                    )
            else:
                logger.warning("image_provider_not_configured", provider="cloudflare-workers-ai")

        if model == "dall-e-3" and settings.openai_api_key:
            try:
                payload = {
                    "model": "dall-e-3",
                    "prompt": clean_prompt[:1000],
                    "n": 1,
                    "size": "1024x1024" if aspect_ratio == "1:1" else "1792x1024",
                    "quality": "standard",
                }
                headers = {
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                }
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/images/generations",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    image_url = response.json()["data"][0]["url"]
                return GeneratedImage(
                    image_url=image_url,
                    provider="openai",
                    model="dall-e-3",
                    prompt=clean_prompt,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    aspect_ratio=aspect_ratio,
                )
            except Exception as exc:
                logger.warning("social_image_provider_fallback", provider="openai", error=str(exc))

        encoded_prompt = urllib.parse.quote(clean_prompt)
        seed = random.SystemRandom().randint(100000, 9999999)
        image_url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&model=flux&nologo=true&seed={seed}&enhance=true"
        )
        return GeneratedImage(
            image_url=image_url,
            provider="pollinations",
            model="flux-realism",
            prompt=clean_prompt,
            latency_ms=int((time.perf_counter() - started) * 1000),
            aspect_ratio=aspect_ratio,
        )


image_generation_service = ImageGenerationService()

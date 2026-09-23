"""AI module — service (multi-provider router with fallback support).

Routes logical AI capabilities to configured providers (OpenAI, Anthropic,
Google Gemini, DeepSeek, Groq, Ollama, OpenRouter, Mistral, LiteLLM).
Supports dynamic runtime configuration from the UI without changing .env.
"""

import json
import re
from typing import Any, AsyncIterator, Optional, TypeVar
from pydantic import BaseModel
import structlog

T = TypeVar("T", bound=BaseModel)

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.modules.ai.contracts import AIProviderContract, AIRequest, AIResponse
from app.modules.ai.providers.implementations import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    DeepSeekProvider,
    GroqProvider,
    OllamaProvider,
    OpenRouterProvider,
    MistralProvider,
    LiteLLMProvider,
)
from app.core.redis import get_redis
from app.modules.social_media.security import decrypt_secret, encrypt_secret

logger = structlog.get_logger()


def _redact_error(value: object) -> str:
    """Remove common credential formats before an error reaches logs/API."""
    text = str(value)
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~-]+", "Bearer [REDACTED]", text)
    text = re.sub(r"(?i)(api[_-]?key|token|secret)=([^&\s]+)", r"\1=[REDACTED]", text)
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    return text[:200]

RECOMMENDED_MODELS: dict[str, list[dict[str, str]]] = {
    "deepseek": [
        {"id": "deepseek-chat", "name": "DeepSeek V3", "speed": "Fast", "capability": "State of the art cost-efficiency"},
        {"id": "deepseek-reasoner", "name": "DeepSeek R1", "speed": "Moderate", "capability": "Chain-of-thought reasoning"},
    ],
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o (Omni)", "speed": "Fast", "capability": "Flagship multimodal"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "speed": "Ultra Fast", "capability": "Lightweight & efficient"},
        {"id": "o1", "name": "o1 Reasoning", "speed": "Moderate", "capability": "Advanced deep logic"},
        {"id": "o3-mini", "name": "o3 Mini", "speed": "Ultra Fast", "capability": "Reasoning flash"},
    ],
    "anthropic": [
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "speed": "Fast", "capability": "Superior copywriting & vision"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "speed": "Ultra Fast", "capability": "Sub-second responsiveness"},
        {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "speed": "Moderate", "capability": "Deep contextual nuance"},
    ],
    "gemini": [
        {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "speed": "Ultra Fast", "capability": "High throughput & cheap"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "speed": "Fast", "capability": "2M token massive context"},
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "speed": "Instant", "capability": "Next-gen real-time speed"},
    ],
    "groq": [
        {"id": "llama-3.3-70b-versatile", "name": "LLaMA 3.3 70B", "speed": "Instant (500+ tok/s)", "capability": "Ultra-fast open weights"},
        {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "speed": "Instant", "capability": "MoE high-speed generation"},
    ],
    "openrouter": [
        {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (via OpenRouter)", "speed": "Fast", "capability": "Universal gateway"},
        {"id": "meta-llama/llama-3.3-70b-instruct", "name": "LLaMA 3.3 70B (OpenRouter)", "speed": "Fast", "capability": "Universal gateway"},
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash (Free)", "speed": "Fast", "capability": "Free tier"},
    ],
    "mistral": [
        {"id": "mistral-large-latest", "name": "Mistral Large", "speed": "Fast", "capability": "Reasoning & multilingual"},
        {"id": "codestral-latest", "name": "Codestral", "speed": "Fast", "capability": "Structured formatting"},
    ],
    "ollama": [
        {"id": "llama3", "name": "LLaMA 3 (Local)", "speed": "Local HW", "capability": "Self-hosted & private"},
        {"id": "mistral", "name": "Mistral 7B (Local)", "speed": "Local HW", "capability": "Self-hosted & private"},
        {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B (Local)", "speed": "Local HW", "capability": "Multilingual local"},
    ],
    "litellm": [
        {"id": "gpt-4o", "name": "LiteLLM Router Default", "speed": "Variable", "capability": "Dynamic backend routing"},
    ],
}


class AIService:
    """Routes AI requests to configured providers with multi-provider fallback and dynamic UI overrides."""

    def __init__(self, providers: Optional[dict[str, AIProviderContract]] = None) -> None:
        self._memory_runtime_settings: dict[str, Any] = {}
        if providers is not None:
            self._providers = providers
        else:
            self._providers = {
                "deepseek": DeepSeekProvider(),
                "openai": OpenAIProvider(),
                "anthropic": AnthropicProvider(),
                "gemini": GeminiProvider(),
                "groq": GroqProvider(),
                "ollama": OllamaProvider(),
                "openrouter": OpenRouterProvider(),
                "mistral": MistralProvider(),
                "litellm": LiteLLMProvider(),
            }

    _RUNTIME_SECRET_KEYS = {
        "deepseek_api_key",
        "openai_api_key",
        "anthropic_api_key",
        "gemini_api_key",
        "groq_api_key",
        "openrouter_api_key",
    }

    async def _load_runtime_settings(self) -> dict[str, Any]:
        """Load runtime overrides and purge legacy plaintext credentials."""
        runtime = dict(self._memory_runtime_settings)
        try:
            r = await get_redis()
            cached = await r.get("winsta:ai_runtime_settings")
            if cached:
                runtime.update(json.loads(cached))
                # Older versions stored API keys directly in Redis. Remove
                # those values immediately; only encrypted suffixes survive.
                legacy_keys = [key for key in runtime if key in self._RUNTIME_SECRET_KEYS]
                if legacy_keys:
                    for key in legacy_keys:
                        runtime.pop(key, None)
                    await r.set("winsta:ai_runtime_settings", json.dumps(runtime))
        except Exception:
            pass
        self._memory_runtime_settings = runtime
        return runtime

    async def get_runtime_settings(self) -> dict[str, Any]:
        """Fetch current dynamic runtime settings from Redis or fallback to config defaults."""
        settings = get_settings()
        runtime = await self._load_runtime_settings()

        active_provider = runtime.get("ai_provider") or settings.ai_provider or "deepseek"
        active_model = runtime.get("ai_model") or settings.ai_model or "deepseek-chat"
        fallback_provider = runtime.get("ai_fallback_provider") or settings.ai_fallback_provider or "openai"
        fallback_model = runtime.get("ai_fallback_model") or settings.ai_fallback_model or "gpt-4o-mini"

        return {
            "ai_provider": active_provider,
            "ai_model": active_model,
            "ai_fallback_provider": fallback_provider,
            "ai_fallback_model": fallback_model,
            "ai_temperature": float(runtime.get("ai_temperature", settings.ai_temperature)),
            "ai_max_tokens": int(runtime.get("ai_max_tokens", settings.ai_max_tokens)),
            "custom_keys_configured": {
                "deepseek": bool(settings.deepseek_api_key or runtime.get("deepseek_api_key__encrypted")),
                "openai": bool(settings.openai_api_key or runtime.get("openai_api_key__encrypted")),
                "anthropic": bool(settings.anthropic_api_key or runtime.get("anthropic_api_key__encrypted")),
                "gemini": bool(settings.gemini_api_key or settings.google_api_key or runtime.get("gemini_api_key__encrypted")),
                "groq": bool(settings.groq_api_key or runtime.get("groq_api_key__encrypted")),
                "openrouter": bool(settings.openrouter_api_key or runtime.get("openrouter_api_key__encrypted")),
            },
        }

    async def update_runtime_settings(self, new_settings: dict[str, Any]) -> dict[str, Any]:
        """Save dynamic runtime settings to Redis and update memory."""
        cleaned: dict[str, Any] = {}
        for key, value in new_settings.items():
            if value is None:
                continue
            if key in self._RUNTIME_SECRET_KEYS:
                # Never keep provider credentials in plaintext in Redis or
                # process logs. Provider adapters can decrypt them on demand.
                cleaned[f"{key}__encrypted"] = encrypt_secret(str(value))
            else:
                cleaned[key] = value
        self._memory_runtime_settings.update(cleaned)
        try:
            r = await get_redis()
            await r.set("winsta:ai_runtime_settings", json.dumps(self._memory_runtime_settings))
        except Exception as e:
            logger.warning("redis_runtime_settings_save_warning", error=str(e))

        # Never emit API keys or other credential material into application
        # logs. Logs are routinely shipped to third-party aggregators.
        safe_settings = {
            key: ("[REDACTED]" if "key" in key.lower() or "secret" in key.lower() or "token" in key.lower() else value)
            for key, value in self._memory_runtime_settings.items()
        }
        logger.info("ai_runtime_settings_updated", settings=safe_settings)
        return await self.get_runtime_settings()

    async def _apply_runtime_credentials(self, runtime: dict[str, Any]) -> None:
        """Apply encrypted admin overrides to provider instances in memory."""
        mapping = {
            "deepseek": "deepseek_api_key",
            "openai": "openai_api_key",
            "anthropic": "anthropic_api_key",
            "gemini": "gemini_api_key",
            "groq": "groq_api_key",
            "openrouter": "openrouter_api_key",
        }
        for provider_name, setting_name in mapping.items():
            encrypted = runtime.get(f"{setting_name}__encrypted")
            provider = self._providers.get(provider_name)
            if not encrypted or provider is None or not hasattr(provider, "settings"):
                continue
            try:
                setattr(provider.settings, setting_name, decrypt_secret(encrypted))
            except Exception:
                logger.warning("ai_runtime_credential_unavailable", provider=provider_name)

    async def get_provider_statuses(self) -> list[dict[str, Any]]:
        """Return all supported providers, their configured status, and recommended models."""
        raw_runtime = await self._load_runtime_settings()
        await self._apply_runtime_credentials(raw_runtime)
        runtime = await self.get_runtime_settings()
        active_prov = runtime.get("ai_provider", "deepseek")
        active_mod = runtime.get("ai_model", "deepseek-chat")

        results = []
        for name, provider in self._providers.items():
            is_avail = await provider.is_available()
            results.append({
                "provider": name,
                "is_configured": is_avail,
                "is_active": name == active_prov,
                "is_fallback": name == runtime.get("ai_fallback_provider"),
                "default_model": active_mod if name == active_prov else (
                    RECOMMENDED_MODELS.get(name, [{}])[0].get("id", "")
                ),
                "models": RECOMMENDED_MODELS.get(name, []),
            })
        return results

    async def generate(
        self,
        capability: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> AIResponse:
        """Generate AI response using specified or dynamically configured runtime provider with fallback."""
        raw_runtime = await self._load_runtime_settings()
        await self._apply_runtime_credentials(raw_runtime)
        runtime = await self.get_runtime_settings()

        temp = temperature if temperature is not None else runtime.get("ai_temperature", 0.7)
        tokens = max_tokens if max_tokens is not None else runtime.get("ai_max_tokens", 2048)

        request = AIRequest(
            capability=capability,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temp,
            max_tokens=tokens,
            response_format=response_format,
        )

        primary = provider_name or runtime.get("ai_provider") or "deepseek"
        primary_model = model_name or runtime.get("ai_model") or ("deepseek-chat" if primary == "deepseek" else "gpt-4o")

        # Build prioritized provider execution chain
        chain = [primary]
        fallback_p = runtime.get("ai_fallback_provider")
        if fallback_p and fallback_p not in chain:
            chain.append(fallback_p)
        for cand_name in ["deepseek", "openai", "groq", "anthropic", "gemini", "openrouter"]:
            if cand_name not in chain:
                chain.append(cand_name)

        last_err: Optional[Exception] = None

        for p_name in chain:
            p_inst = self._providers.get(p_name.lower())
            if not p_inst:
                continue

            # Check if this provider has an API key configured
            if not await p_inst.is_available():
                continue

            target_model = (
                primary_model
                if p_name == primary
                else RECOMMENDED_MODELS.get(p_name, [{}])[0].get("id", "default")
            )

            try:
                response = await p_inst.generate(request, target_model)
                logger.info(
                    "ai_request_success",
                    capability=capability,
                    provider=p_name,
                    model=target_model,
                    latency_ms=response.latency_ms,
                )
                return response
            except Exception as e:
                logger.warning(
                    "ai_provider_attempt_failed",
                    provider=p_name,
                    capability=capability,
                    model=target_model,
                    error=_redact_error(e),
                )
                last_err = e

        raise ExternalServiceException(
            message="All configured AI providers failed. Check provider configuration and try again."
        )

    async def generate_stream(
        self,
        capability: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream tokens in real-time with multi-provider fallback before the first chunk."""
        raw_runtime = await self._load_runtime_settings()
        await self._apply_runtime_credentials(raw_runtime)
        runtime = await self.get_runtime_settings()

        temp = temperature if temperature is not None else runtime.get("ai_temperature", 0.7)
        tokens = max_tokens if max_tokens is not None else runtime.get("ai_max_tokens", 2048)

        request = AIRequest(
            capability=capability,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temp,
            max_tokens=tokens,
            stream=True,
        )

        primary = provider_name or runtime.get("ai_provider") or "deepseek"
        primary_model = model_name or runtime.get("ai_model") or ("deepseek-chat" if primary == "deepseek" else "gpt-4o")

        chain = [primary]
        fallback_p = runtime.get("ai_fallback_provider")
        if fallback_p and fallback_p not in chain:
            chain.append(fallback_p)
        for cand_name in ["deepseek", "openai", "groq", "anthropic", "gemini", "openrouter"]:
            if cand_name not in chain:
                chain.append(cand_name)

        started = False
        for p_name in chain:
            p_inst = self._providers.get(p_name.lower())
            if not p_inst or not await p_inst.is_available():
                continue

            target_model = (
                primary_model
                if p_name == primary
                else RECOMMENDED_MODELS.get(p_name, [{}])[0].get("id", "default")
            )

            try:
                stream_gen = p_inst.generate_stream(request, target_model)
                async for token in stream_gen:
                    started = True
                    yield token
                logger.info("ai_stream_success", capability=capability, provider=p_name, model=target_model)
                return
            except Exception as e:
                logger.warning(
                    "ai_stream_provider_failed",
                    provider=p_name,
                    capability=capability,
                    model=target_model,
                    error=_redact_error(e),
                )
                if started:
                    # Stream was interrupted midway after client received partial data
                    raise ExternalServiceException(message=f"AI stream interrupted: {_redact_error(e)}")

        raise ExternalServiceException(
            message="All configured AI providers failed for streaming. Check provider configuration and try again."
        )

    async def generate_structured(
        self,
        capability: str,
        prompt: str,
        schema: type[T],
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 2,
    ) -> T:
        """Generate structured data guaranteed to conform to a Pydantic schema."""
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        augmented_system_prompt = (
            f"{system_prompt or ''}\n\n"
            f"You MUST respond ONLY with a valid JSON object strictly matching this schema:\n"
            f"{schema_json}\n"
            f"Do not wrap in markdown or backticks. Return valid JSON only."
        ).strip()

        last_error = None
        for attempt in range(max_retries + 1):
            retry_prompt = prompt
            if attempt > 0 and last_error:
                retry_prompt = f"{prompt}\n\n[Previous response failed validation with error: {last_error}. Please correct the output to strictly conform to the schema.]"

            response = await self.generate(
                capability=capability,
                prompt=retry_prompt,
                system_prompt=augmented_system_prompt,
                provider_name=provider_name,
                model_name=model_name,
                temperature=temperature if temperature is not None else 0.2,
                response_format="json",
            )

            try:
                clean_content = response.content.strip()
                if clean_content.startswith("```"):
                    clean_content = re.sub(r"^```(?:json)?\n?", "", clean_content)
                    clean_content = re.sub(r"\n?```$", "", clean_content)
                parsed = schema.model_validate_json(clean_content)
                return parsed
            except Exception as err:
                last_error = str(err)
                logger.warning("ai_structured_validation_retry", attempt=attempt, error=last_error)

        raise ExternalServiceException(
            message=f"Failed to generate structured data matching {schema.__name__}: {last_error}"
        )

    def _get_provider(self, provider_name: str) -> AIProviderContract:
        provider = self._providers.get(provider_name.lower())
        if not provider:
            raise ExternalServiceException(
                message=f"AI provider '{provider_name}' is not supported or not registered"
            )
        return provider


ai_service = AIService()

"""AI Providers — Multi-Provider LLM Implementations.

Production adapters for OpenAI, Anthropic, Google Gemini, DeepSeek,
Groq, Ollama, OpenRouter, Mistral, and LiteLLM with HTTP connection pooling
and real-time token streaming.
"""

import json
import time
from typing import Any, AsyncIterator, Optional
import httpx
import structlog

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.modules.ai.contracts import AIProviderContract, AIRequest, AIResponse
from app.modules.ai.providers.http_client import get_ai_http_client

logger = structlog.get_logger()


async def _stream_openai_sse(response: httpx.Response) -> AsyncIterator[str]:
    """Parse OpenAI-compatible Server-Sent Events (SSE) data stream."""
    async for line in response.aiter_lines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            break
        try:
            chunk = json.loads(data_str)
            choices = chunk.get("choices") or []
            if choices:
                delta = choices[0].get("delta") or {}
                content = delta.get("content")
                if content:
                    yield content
        except Exception:
            continue


async def _stream_anthropic_sse(response: httpx.Response) -> AsyncIterator[str]:
    """Parse Anthropic Claude Server-Sent Events stream."""
    async for line in response.aiter_lines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        try:
            data = json.loads(data_str)
            event_type = data.get("type")
            if event_type == "content_block_delta":
                delta = data.get("delta") or {}
                if delta.get("type") == "text_delta":
                    text = delta.get("text")
                    if text:
                        yield text
        except Exception:
            continue


async def _stream_gemini_sse(response: httpx.Response) -> AsyncIterator[str]:
    """Parse Google Gemini Server-Sent Events stream."""
    async for line in response.aiter_lines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        try:
            data = json.loads(data_str)
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0].get("content", {}).get("parts") or []
                for p in parts:
                    text = p.get("text")
                    if text:
                        yield text
        except Exception:
            continue


async def _stream_ollama_json(response: httpx.Response) -> AsyncIterator[str]:
    """Parse line-delimited JSON stream from Ollama."""
    async for line in response.aiter_lines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            content = data.get("message", {}).get("content")
            if content:
                yield content
            if data.get("done"):
                break
        except Exception:
            continue


# ---------------------------------------------------------------------------
# 1. OpenAI Provider
# ---------------------------------------------------------------------------
class OpenAIProvider(AIProviderContract):
    """OpenAI API provider adapter (GPT-4o, GPT-4o-mini, o1, etc.)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "openai"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.openai_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any], dict[str, str]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="OpenAI API key is not configured")

        base_url = (self.settings.openai_api_base or "https://api.openai.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, Any] = {
            "model": model or self.settings.ai_model or "gpt-4o",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

        if request.response_format == "json" and not stream:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return url, payload, headers

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload, headers = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers=headers)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("openai_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"OpenAI API error ({resp.status_code})")

        data = resp.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content", "")
        usage = data.get("usage", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=usage.get("prompt_tokens", len(request.prompt.split())),
            output_tokens=usage.get("completion_tokens", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload, headers = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers=headers)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"OpenAI streaming error ({resp.status_code})")

        try:
            async for token in _stream_openai_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 2. Anthropic Provider
# ---------------------------------------------------------------------------
class AnthropicProvider(AIProviderContract):
    """Anthropic Claude provider adapter (Claude 3.5 Sonnet, Claude 3 Opus, etc.)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.anthropic_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any], dict[str, str]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="Anthropic API key is not configured")

        base_url = (self.settings.anthropic_api_base or "https://api.anthropic.com/v1").rstrip("/")
        url = f"{base_url}/messages"

        payload: dict[str, Any] = {
            "model": model or "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": stream,
        }

        if request.system_prompt:
            payload["system"] = request.system_prompt

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        return url, payload, headers

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload, headers = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers=headers)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("anthropic_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"Anthropic API error ({resp.status_code})")

        data = resp.json()
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=usage.get("input_tokens", len(request.prompt.split())),
            output_tokens=usage.get("output_tokens", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload, headers = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers=headers)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"Anthropic streaming error ({resp.status_code})")

        try:
            async for token in _stream_anthropic_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 3. Google Gemini Provider
# ---------------------------------------------------------------------------
class GeminiProvider(AIProviderContract):
    """Google Gemini provider adapter (Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 2.0)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.gemini_api_key or self.settings.google_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_url_and_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="Gemini / Google AI API key is not configured")

        gemini_model = model or "gemini-1.5-flash"
        model_path = gemini_model.replace("models/", "") if gemini_model.startswith("models/") else gemini_model

        endpoint = "streamGenerateContent?alt=sse&" if stream else "generateContent?"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_path}:{endpoint}key={api_key}"

        contents = []
        if request.system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System Instruction: {request.system_prompt}\n\nTask: {request.prompt}"}]
            })
        else:
            contents.append({
                "role": "user",
                "parts": [{"text": request.prompt}]
            })

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }

        if request.response_format == "json" and not stream:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        return url, payload

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload = self._build_url_and_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("gemini_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"Gemini API error ({resp.status_code})")

        data = resp.json()
        content = ""
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                content = "".join([p.get("text", "") for p in parts])
        except Exception as e:
            logger.warning("gemini_parse_warning", error=str(e))

        usage = data.get("usageMetadata", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or "gemini-1.5-flash",
            input_tokens=usage.get("promptTokenCount", len(request.prompt.split())),
            output_tokens=usage.get("candidatesTokenCount", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload = self._build_url_and_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers={"Content-Type": "application/json"})
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"Gemini streaming error ({resp.status_code})")

        try:
            async for token in _stream_gemini_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 4. DeepSeek Provider
# ---------------------------------------------------------------------------
class DeepSeekProvider(AIProviderContract):
    """DeepSeek provider adapter (DeepSeek-V3, DeepSeek-R1)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "deepseek"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.deepseek_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any], dict[str, str]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="DeepSeek API key is not configured")

        base_url = (self.settings.deepseek_api_base or "https://api.deepseek.com/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model or "deepseek-chat",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

        if request.response_format == "json" and not stream:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return url, payload, headers

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload, headers = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers=headers)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("deepseek_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"DeepSeek API error ({resp.status_code})")

        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        usage = data.get("usage", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=usage.get("prompt_tokens", len(request.prompt.split())),
            output_tokens=usage.get("completion_tokens", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload, headers = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers=headers)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"DeepSeek streaming error ({resp.status_code})")

        try:
            async for token in _stream_openai_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 5. Groq Provider
# ---------------------------------------------------------------------------
class GroqProvider(AIProviderContract):
    """Groq ultra-fast inference provider adapter (LLaMA 3.3 70B, Mixtral, etc.)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "groq"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.groq_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any], dict[str, str]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="Groq API key is not configured")

        base_url = (self.settings.groq_api_base or "https://api.groq.com/openai/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model or "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

        if request.response_format == "json" and not stream:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return url, payload, headers

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload, headers = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers=headers)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("groq_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"Groq API error ({resp.status_code})")

        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        usage = data.get("usage", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=usage.get("prompt_tokens", len(request.prompt.split())),
            output_tokens=usage.get("completion_tokens", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload, headers = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers=headers)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"Groq streaming error ({resp.status_code})")

        try:
            async for token in _stream_openai_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 6. OpenRouter Provider
# ---------------------------------------------------------------------------
class OpenRouterProvider(AIProviderContract):
    """OpenRouter universal gateway adapter (Access to hundreds of models)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.openrouter_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any], dict[str, str]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="OpenRouter API key is not configured")

        base_url = (self.settings.openrouter_api_base or "https://openrouter.ai/api/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model or "anthropic/claude-3.5-sonnet",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

        if request.response_format == "json" and not stream:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://winsta.ai",
            "X-Title": "Winsta AI Studio",
            "Content-Type": "application/json",
        }
        return url, payload, headers

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload, headers = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers=headers)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("openrouter_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"OpenRouter API error ({resp.status_code})")

        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        usage = data.get("usage", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=usage.get("prompt_tokens", len(request.prompt.split())),
            output_tokens=usage.get("completion_tokens", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload, headers = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers=headers)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"OpenRouter streaming error ({resp.status_code})")

        try:
            async for token in _stream_openai_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 7. Mistral Provider
# ---------------------------------------------------------------------------
class MistralProvider(AIProviderContract):
    """Mistral AI provider adapter (Mistral Large, Codestral, etc.)."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "mistral"

    def _get_api_key(self) -> Optional[str]:
        return self.settings.mistral_api_key or self.settings.ai_api_key

    async def is_available(self) -> bool:
        return bool(self._get_api_key())

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any], dict[str, str]]:
        api_key = self._get_api_key()
        if not api_key:
            raise ExternalServiceException(message="Mistral API key is not configured")

        base_url = (self.settings.mistral_api_base or "https://api.mistral.ai/v1").rstrip("/")
        url = f"{base_url}/chat/completions"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model or "mistral-large-latest",
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": stream,
        }

        if request.response_format == "json" and not stream:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return url, payload, headers

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload, headers = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload, headers=headers)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("mistral_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"Mistral API error ({resp.status_code})")

        data = resp.json()
        content = data["choices"][0]["message"].get("content", "")
        usage = data.get("usage", {})

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=usage.get("prompt_tokens", len(request.prompt.split())),
            output_tokens=usage.get("completion_tokens", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload, headers = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload, headers=headers)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"Mistral streaming error ({resp.status_code})")

        try:
            async for token in _stream_openai_sse(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 8. Ollama Provider (Self-hosted)
# ---------------------------------------------------------------------------
class OllamaProvider(AIProviderContract):
    """Local / Self-hosted Ollama LLM provider adapter."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def is_available(self) -> bool:
        base_url = (self.settings.ollama_base_url or "http://localhost:11434").rstrip("/")
        try:
            client = await get_ai_http_client(3.0)
            res = await client.get(f"{base_url}/api/tags")
            return res.status_code == 200
        except Exception:
            return False

    def _build_payload(self, request: AIRequest, model: str, stream: bool = False) -> tuple[str, dict[str, Any]]:
        base_url = (self.settings.ollama_base_url or "http://localhost:11434").rstrip("/")
        url = f"{base_url}/api/chat"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": model or "llama3",
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        if request.response_format == "json":
            payload["format"] = "json"

        return url, payload

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        url, payload = self._build_payload(request, model, stream=False)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)

        start = time.perf_counter()
        resp = await client.post(url, json=payload)
        latency = int((time.perf_counter() - start) * 1000)

        if resp.status_code != 200:
            logger.error("ollama_api_error", status=resp.status_code)
            raise ExternalServiceException(message=f"Ollama API error ({resp.status_code})")

        data = resp.json()
        content = data.get("message", {}).get("content", "")

        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model or payload["model"],
            input_tokens=data.get("prompt_eval_count", len(request.prompt.split())),
            output_tokens=data.get("eval_count", len(content.split())),
            latency_ms=latency,
            raw_response=data,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        url, payload = self._build_payload(request, model, stream=True)
        client = await get_ai_http_client(self.settings.ai_timeout_seconds)
        req = client.build_request("POST", url, json=payload)
        resp = await client.send(req, stream=True)

        if resp.status_code != 200:
            await resp.aread()
            raise ExternalServiceException(message=f"Ollama streaming error ({resp.status_code})")

        try:
            async for token in _stream_ollama_json(resp):
                yield token
        finally:
            await resp.aclose()


# ---------------------------------------------------------------------------
# 9. LiteLLM Provider
# ---------------------------------------------------------------------------
class LiteLLMProvider(AIProviderContract):
    """LiteLLM Unified router provider adapter."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return "litellm"

    async def is_available(self) -> bool:
        return True

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        try:
            import litellm
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            start = time.perf_counter()
            response = await litellm.acompletion(
                model=model or "gpt-4o",
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                api_key=self.settings.ai_api_key or self.settings.openai_api_key,
            )
            latency = int((time.perf_counter() - start) * 1000)

            content = response.choices[0].message.content or ""
            usage = response.usage

            return AIResponse(
                content=content,
                provider=self.provider_name,
                model=model,
                input_tokens=getattr(usage, "prompt_tokens", len(request.prompt.split())),
                output_tokens=getattr(usage, "completion_tokens", len(content.split())),
                latency_ms=latency,
            )
        except Exception as e:
            logger.error("litellm_execution_error", error=str(e))
            raise ExternalServiceException(message=f"LiteLLM call failed: {str(e)}")

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        try:
            import litellm
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            response = await litellm.acompletion(
                model=model or "gpt-4o",
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                api_key=self.settings.ai_api_key or self.settings.openai_api_key,
                stream=True,
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error("litellm_stream_error", error=str(e))
            raise ExternalServiceException(message=f"LiteLLM streaming failed: {str(e)}")

# Real OpenAI and Anthropic clients for production LLM calls.
# Mock clients stay schema-compatible while these classes handle live upstream traffic.

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from app.integrations.http import request, stream_lines
from app.integrations.llm.base import LLMProviderError


@dataclass(frozen=True)
class OpenAIClient:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 60.0
    provider: str = "openai"

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await request(
                provider=self.provider,
                method="POST",
                url=f"{self.base_url.rstrip('/')}/chat/completions",
                timeout_seconds=self.timeout_seconds,
                headers=self.headers(),
                json_body=payload,
                request_body_for_logs=payload,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("OpenAI chat completion response was not a JSON object.")
            return body
        except httpx.HTTPStatusError as exc:
            raise llm_provider_http_error(self.provider, exc.response) from exc
        except (httpx.TransportError, TypeError, ValueError) as exc:
            raise LLMProviderError(
                provider=self.provider,
                detail=f"{self.provider} provider is unavailable.",
            ) from exc

    async def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        async for line in stream_lines(
            provider=self.provider,
            method="POST",
            url=f"{self.base_url.rstrip('/')}/chat/completions",
            timeout_seconds=self.timeout_seconds,
            headers=self.headers(),
            json_body={**payload, "stream": True},
            request_body_for_logs={**payload, "stream": True},
        ):
            yield f"{line}\n"

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("OpenAIClient does not implement Anthropic Messages.")

    async def anthropic_message_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        if payload.get("__unsupported_stream_sentinel__") is True:
            yield ""
        raise NotImplementedError("OpenAIClient does not implement Anthropic Messages streaming.")

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


@dataclass(frozen=True)
class AnthropicClient:
    api_key: str
    base_url: str = "https://api.anthropic.com/v1"
    anthropic_version: str = "2023-06-01"
    timeout_seconds: float = 60.0
    provider: str = "anthropic"

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("AnthropicClient does not implement OpenAI Chat Completions.")

    async def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        if payload.get("__unsupported_stream_sentinel__") is True:
            yield ""
        raise NotImplementedError(
            "AnthropicClient does not implement OpenAI Chat Completions streaming."
        )

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await request(
                provider=self.provider,
                method="POST",
                url=f"{self.base_url.rstrip('/')}/messages",
                timeout_seconds=self.timeout_seconds,
                headers=self.headers(),
                json_body=payload,
                request_body_for_logs=payload,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("Anthropic message response was not a JSON object.")
            return body
        except httpx.HTTPStatusError as exc:
            raise llm_provider_http_error(self.provider, exc.response) from exc
        except (httpx.TransportError, TypeError, ValueError) as exc:
            raise LLMProviderError(
                provider=self.provider,
                detail=f"{self.provider} provider is unavailable.",
            ) from exc

    async def anthropic_message_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        async for line in stream_lines(
            provider=self.provider,
            method="POST",
            url=f"{self.base_url.rstrip('/')}/messages",
            timeout_seconds=self.timeout_seconds,
            headers=self.headers(),
            json_body={**payload, "stream": True},
            request_body_for_logs={**payload, "stream": True},
        ):
            yield f"{line}\n"

    def headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
        }


def llm_provider_http_error(provider: str, response: httpx.Response) -> LLMProviderError:
    provider_message = provider_error_message(response)
    detail = f"{provider} provider returned HTTP {response.status_code}."
    if provider_message:
        detail = f"{detail} {provider_message}"
    return LLMProviderError(provider=provider, detail=detail, status_code=response.status_code)


def provider_error_message(response: httpx.Response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        error = body.get("error")
        error_message = error.get("message") if isinstance(error, dict) else None
        if isinstance(error_message, str):
            return error_message
        message = body.get("message")
        if isinstance(message, str):
            return message
    return None

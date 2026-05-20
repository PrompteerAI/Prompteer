from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class OpenAIClient:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 60.0
    provider: str = "openai"

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=self.headers(),
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("OpenAI chat completion response was not a JSON object.")
            return body

    async def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        async with (
            httpx.AsyncClient(timeout=self.timeout_seconds) as client,
            client.stream(
                "POST",
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers=self.headers(),
                json={**payload, "stream": True},
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
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
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url.rstrip('/')}/messages",
                headers=self.headers(),
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TypeError("Anthropic message response was not a JSON object.")
            return body

    async def anthropic_message_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        async with (
            httpx.AsyncClient(timeout=self.timeout_seconds) as client,
            client.stream(
                "POST",
                f"{self.base_url.rstrip('/')}/messages",
                headers=self.headers(),
                json={**payload, "stream": True},
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                yield f"{line}\n"

    def headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
        }

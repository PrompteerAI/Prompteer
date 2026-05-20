"""Protocol for chat-completion clients used by prompt challenge runs."""

from collections.abc import AsyncIterator
from typing import Any, Protocol


class LLMClient(Protocol):
    @property
    def provider(self) -> str:
        """The selected provider name for boot logs and diagnostics."""

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an OpenAI-compatible Chat Completions response."""

    def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Stream OpenAI-compatible Chat Completions SSE events."""

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an Anthropic-compatible Messages response."""

    def anthropic_message_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        """Stream Anthropic-compatible Messages SSE events."""

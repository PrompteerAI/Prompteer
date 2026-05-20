"""Deterministic OpenAI and Anthropic LLM mocks.

Schema references verified on 2026-05-20:
- OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat/create
- Anthropic Messages: https://docs.anthropic.com/en/api/messages
- Anthropic Messages streaming: https://docs.anthropic.com/en/docs/build-with-claude/streaming

The mock exposes upstream-shaped methods and dev-only HTTP routes so local
development can exercise the same request/response contracts as real providers.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.feature_flags import dev_routes_enabled

OPENAI_BASE_CREATED_AT = 1_735_689_600

router = APIRouter(tags=["mock-llm"])


class LLMMockValidationError(ValueError):
    pass


@dataclass(frozen=True)
class MockLLMClient:
    provider: str = "mock"

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = normalize_openai_request(payload)
        response_text, finish_reason = openai_response_text(request)
        digest = stable_digest(request)
        completion_tokens = token_count(response_text)
        prompt_tokens = token_count(extract_openai_prompt(request))
        choices = [
            {
                "index": index,
                "message": {
                    "role": "assistant",
                    "content": response_text if index == 0 else f"{response_text} [{index + 1}]",
                    "refusal": None,
                },
                "finish_reason": finish_reason,
                "logprobs": None,
            }
            for index in range(int(request.get("n", 1)))
        ]
        return {
            "id": f"chatcmpl_mock_{digest[:24]}",
            "object": "chat.completion",
            "created": stable_created_at(request, OPENAI_BASE_CREATED_AT),
            "model": request["model"],
            "choices": choices,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens * len(choices),
                "total_tokens": prompt_tokens + completion_tokens * len(choices),
            },
            "system_fingerprint": f"fp_mock_{digest[:10]}",
        }

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = normalize_anthropic_request(payload)
        response_text, stop_reason, stop_sequence = anthropic_response_text(request)
        digest = stable_digest(request)
        return {
            "id": f"msg_mock_{digest[:24]}",
            "type": "message",
            "role": "assistant",
            "model": request["model"],
            "content": [{"type": "text", "text": response_text}],
            "stop_reason": stop_reason,
            "stop_sequence": stop_sequence,
            "usage": {
                "input_tokens": token_count(extract_anthropic_prompt(request)),
                "output_tokens": token_count(response_text),
            },
        }

    async def chat_completion_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        request = normalize_openai_request({**payload, "stream": True})
        response = await self.chat_completion(request)
        response_text = str(response["choices"][0]["message"]["content"])
        base_chunk = {
            "id": response["id"],
            "object": "chat.completion.chunk",
            "created": response["created"],
            "model": response["model"],
            "system_fingerprint": response["system_fingerprint"],
        }
        yield sse_data(
            {
                **base_chunk,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            }
        )
        for chunk in split_text(response_text):
            yield sse_data(
                {
                    **base_chunk,
                    "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}],
                }
            )
        final_chunk = {
            **base_chunk,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        if include_openai_stream_usage(request):
            final_chunk["usage"] = response["usage"]
        yield sse_data(final_chunk)
        yield "data: [DONE]\n\n"

    async def anthropic_message_stream(self, payload: dict[str, Any]) -> AsyncIterator[str]:
        request = normalize_anthropic_request({**payload, "stream": True})
        message = await self.anthropic_message(request)
        response_text = str(message["content"][0]["text"])
        started_message = {**message, "content": [], "stop_reason": None, "stop_sequence": None}
        yield anthropic_sse("message_start", {"type": "message_start", "message": started_message})
        yield anthropic_sse(
            "content_block_start",
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            },
        )
        for chunk in split_text(response_text):
            yield anthropic_sse(
                "content_block_delta",
                {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": chunk},
                },
            )
        yield anthropic_sse("content_block_stop", {"type": "content_block_stop", "index": 0})
        yield anthropic_sse(
            "message_delta",
            {
                "type": "message_delta",
                "delta": {
                    "stop_reason": message["stop_reason"],
                    "stop_sequence": message["stop_sequence"],
                },
                "usage": {"output_tokens": message["usage"]["output_tokens"]},
            },
        )
        yield anthropic_sse("message_stop", {"type": "message_stop"})


def require_mock_routes() -> None:
    if not dev_routes_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.post("/v1/chat/completions", response_model=None)
async def openai_chat_completions(payload: dict[str, Any]) -> dict[str, Any] | StreamingResponse:
    require_mock_routes()
    client = MockLLMClient()
    try:
        if payload.get("stream") is True:
            return StreamingResponse(
                client.chat_completion_stream(payload),
                media_type="text/event-stream",
            )
        return await client.chat_completion(payload)
    except LLMMockValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/v1/messages", response_model=None)
async def anthropic_messages(payload: dict[str, Any]) -> dict[str, Any] | StreamingResponse:
    require_mock_routes()
    client = MockLLMClient()
    try:
        if payload.get("stream") is True:
            return StreamingResponse(
                client.anthropic_message_stream(payload),
                media_type="text/event-stream",
            )
        return await client.anthropic_message(payload)
    except LLMMockValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def normalize_openai_request(payload: dict[str, Any]) -> dict[str, Any]:
    model = payload.get("model")
    if not isinstance(model, str) or not model:
        raise LLMMockValidationError("OpenAI chat completion requests require a model.")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise LLMMockValidationError("OpenAI chat completion requests require messages[].")
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("role"), str):
            raise LLMMockValidationError("Each OpenAI message must include a role.")
    n = payload.get("n", 1)
    if not isinstance(n, int) or n < 1 or n > 8:
        raise LLMMockValidationError("OpenAI n must be an integer between 1 and 8.")
    return {**payload, "model": model, "messages": messages, "n": n}


def normalize_anthropic_request(payload: dict[str, Any]) -> dict[str, Any]:
    model = payload.get("model")
    if not isinstance(model, str) or not model:
        raise LLMMockValidationError("Anthropic message requests require a model.")
    max_tokens = payload.get("max_tokens")
    if not isinstance(max_tokens, int) or max_tokens < 1:
        raise LLMMockValidationError("Anthropic message requests require max_tokens >= 1.")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise LLMMockValidationError("Anthropic message requests require messages[].")
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in {"user", "assistant"}:
            raise LLMMockValidationError("Each Anthropic message must use role user or assistant.")
    return {**payload, "model": model, "max_tokens": max_tokens, "messages": messages}


def openai_response_text(request: dict[str, Any]) -> tuple[str, str]:
    prompt = extract_openai_prompt(request)
    digest = stable_digest(request)[:12]
    text = f"Mock Prompteer response {digest}: {summarize_prompt(prompt)}"
    text, finish_reason = apply_openai_limits(text, request)
    return text, finish_reason


def anthropic_response_text(request: dict[str, Any]) -> tuple[str, str, str | None]:
    prompt = extract_anthropic_prompt(request)
    digest = stable_digest(request)[:12]
    text = f"Mock Prompteer response {digest}: {summarize_prompt(prompt)}"
    stop_sequence = None
    stop_reason = "end_turn"
    for candidate in as_string_list(request.get("stop_sequences")):
        if candidate and candidate in text:
            text = text.split(candidate, 1)[0]
            stop_reason = "stop_sequence"
            stop_sequence = candidate
            break
    max_tokens = int(request["max_tokens"])
    words = text.split()
    if len(words) > max_tokens:
        text = " ".join(words[:max_tokens])
        stop_reason = "max_tokens"
        stop_sequence = None
    return text, stop_reason, stop_sequence


def apply_openai_limits(text: str, request: dict[str, Any]) -> tuple[str, str]:
    for candidate in as_string_list(request.get("stop")):
        if candidate and candidate in text:
            return text.split(candidate, 1)[0], "stop"
    max_tokens = request.get("max_tokens") or request.get("max_completion_tokens")
    if isinstance(max_tokens, int) and max_tokens > 0:
        words = text.split()
        if len(words) > max_tokens:
            return " ".join(words[:max_tokens]), "length"
    return text, "stop"


def extract_openai_prompt(request: dict[str, Any]) -> str:
    parts: list[str] = []
    for message in request["messages"]:
        if isinstance(message, dict):
            content = message.get("content")
            parts.extend(extract_content_text(content))
    return "\n".join(parts)


def extract_anthropic_prompt(request: dict[str, Any]) -> str:
    parts: list[str] = []
    system = request.get("system")
    parts.extend(extract_content_text(system))
    for message in request["messages"]:
        if isinstance(message, dict):
            parts.extend(extract_content_text(message.get("content")))
    return "\n".join(parts)


def extract_content_text(content: Any) -> list[str]:
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"text", "input_text"} and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return parts
    return []


def summarize_prompt(prompt: str) -> str:
    normalized = " ".join(prompt.split())
    if not normalized:
        return "No prompt content was provided."
    return normalized[:180]


def stable_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


def stable_created_at(payload: dict[str, Any], base: int) -> int:
    return base + int(stable_digest(payload)[:8], 16) % 31_536_000


def token_count(text: str) -> int:
    return max(1, len(text.split()))


def split_text(text: str, *, chunk_size: int = 24) -> Iterable[str]:
    for start in range(0, len(text), chunk_size):
        yield text[start : start + chunk_size]


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return []


def include_openai_stream_usage(request: dict[str, Any]) -> bool:
    stream_options = request.get("stream_options")
    return isinstance(stream_options, dict) and stream_options.get("include_usage") is True


def sse_data(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, separators=(',', ':'), sort_keys=True)}\n\n"


def anthropic_sse(event: str, payload: dict[str, Any]) -> str:
    data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return f"event: {event}\ndata: {data}\n\n"

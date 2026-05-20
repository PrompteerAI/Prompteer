"""Tests for OpenAI and Anthropic compatible LLM mocks and real clients."""

import json
from typing import Any

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations.llm import get_llm_client
from app.integrations.llm.mock import MockLLMClient
from app.integrations.llm.real import AnthropicClient, OpenAIClient
from app.main import create_app

OPENAI_PAYLOAD: dict[str, Any] = {
    "model": "gpt-4.1-mini",
    "messages": [
        {"role": "system", "content": "You are a concise prompt reviewer."},
        {"role": "user", "content": "Rewrite this prompt for a FizzBuzz coding task."},
    ],
}

ANTHROPIC_PAYLOAD: dict[str, Any] = {
    "model": "claude-3-7-sonnet-latest",
    "max_tokens": 64,
    "system": "You are a concise prompt reviewer.",
    "messages": [{"role": "user", "content": "Improve this image prompt."}],
}


@pytest.fixture(autouse=True)
def enable_dev_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)


@pytest.mark.asyncio
async def test_openai_mock_is_deterministic_and_schema_compatible() -> None:
    client = MockLLMClient()

    first = await client.chat_completion(OPENAI_PAYLOAD)
    second = await client.chat_completion(OPENAI_PAYLOAD)

    assert first == second
    assert first["object"] == "chat.completion"
    assert first["id"].startswith("chatcmpl_mock_")
    assert first["model"] == "gpt-4.1-mini"
    assert first["choices"][0]["message"]["role"] == "assistant"
    assert "Mock Prompteer response" in first["choices"][0]["message"]["content"]
    assert first["choices"][0]["finish_reason"] == "stop"
    assert set(first["usage"]) == {"prompt_tokens", "completion_tokens", "total_tokens"}
    assert first["system_fingerprint"].startswith("fp_mock_")


@pytest.mark.asyncio
async def test_anthropic_mock_is_deterministic_and_schema_compatible() -> None:
    client = MockLLMClient()

    first = await client.anthropic_message(ANTHROPIC_PAYLOAD)
    second = await client.anthropic_message(ANTHROPIC_PAYLOAD)

    assert first == second
    assert first["id"].startswith("msg_mock_")
    assert first["type"] == "message"
    assert first["role"] == "assistant"
    assert first["model"] == "claude-3-7-sonnet-latest"
    assert first["content"][0]["type"] == "text"
    assert "Mock Prompteer response" in first["content"][0]["text"]
    assert first["stop_reason"] == "end_turn"
    assert set(first["usage"]) == {"input_tokens", "output_tokens"}


def test_mock_llm_dev_routes_include_streaming_sse() -> None:
    client = TestClient(create_app())

    openai_response = client.post("/v1/chat/completions", json=OPENAI_PAYLOAD)
    assert openai_response.status_code == 200
    assert openai_response.json()["object"] == "chat.completion"

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={**OPENAI_PAYLOAD, "stream": True, "stream_options": {"include_usage": True}},
    ) as response:
        body = "".join(response.iter_text())
    assert "chat.completion.chunk" in body
    assert "data: [DONE]" in body

    with client.stream(
        "POST",
        "/v1/messages",
        json={**ANTHROPIC_PAYLOAD, "stream": True},
    ) as response:
        anthropic_body = "".join(response.iter_text())
    assert "event: message_start" in anthropic_body
    assert "event: content_block_delta" in anthropic_body
    assert "event: message_stop" in anthropic_body


def test_llm_factory_selects_real_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    assert isinstance(get_llm_client(), OpenAIClient)

    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")
    assert isinstance(get_llm_client(), AnthropicClient)

    monkeypatch.setattr(settings, "anthropic_api_key", "")
    assert isinstance(get_llm_client(), MockLLMClient)


@pytest.mark.asyncio
async def test_openai_real_client_posts_to_chat_completions() -> None:
    expected = {"id": "chatcmpl_test", "object": "chat.completion"}
    with respx.mock:
        route = respx.post("https://openai.example/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=expected)
        )
        client = OpenAIClient(api_key="sk-test", base_url="https://openai.example/v1")

        result = await client.chat_completion(OPENAI_PAYLOAD)

    assert result == expected
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer sk-test"
    assert json.loads(request.content)["model"] == "gpt-4.1-mini"


@pytest.mark.asyncio
async def test_anthropic_real_client_posts_to_messages() -> None:
    expected = {"id": "msg_test", "type": "message"}
    with respx.mock:
        route = respx.post("https://anthropic.example/v1/messages").mock(
            return_value=httpx.Response(200, json=expected)
        )
        client = AnthropicClient(
            api_key="sk-ant-test",
            base_url="https://anthropic.example/v1",
            anthropic_version="2023-06-01",
        )

        result = await client.anthropic_message(ANTHROPIC_PAYLOAD)

    assert result == expected
    request = route.calls.last.request
    assert request.headers["x-api-key"] == "sk-ant-test"
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert json.loads(request.content)["model"] == "claude-3-7-sonnet-latest"

# Tests for the shared outbound HTTP helper used by real upstream clients.
# They lock down retry scope and log redaction without hitting external networks.

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx

from app.integrations import http as outbound_http
from app.integrations.http import RetryPolicy, body_preview, request, stream_lines


class CaptureLogger:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []

    def info(self, event: str, **kwargs: Any) -> None:
        self.events.append((event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        self.events.append((event, kwargs))


def test_body_preview_redacts_sensitive_payload_fields() -> None:
    preview = body_preview(
        {
            "api_key": "sk-live-secret",
            "apiKey": "sk-live-camel",
            "clientSecret": "oauth-client-secret",
            "messages": [{"role": "user", "content": "private prompt"}],
            "metadata": {
                "safe": "visible",
                "customerEmail": "paid@prompteer.dev",
                "accessToken": "ya29.private",
            },
        }
    )

    assert preview is not None
    assert "sk-live-secret" not in preview
    assert "sk-live-camel" not in preview
    assert "oauth-client-secret" not in preview
    assert "private prompt" not in preview
    assert "paid@prompteer.dev" not in preview
    assert "ya29.private" not in preview
    assert '"api_key":"[redacted]"' in preview
    assert '"apiKey":"[redacted]"' in preview
    assert '"clientSecret":"[redacted]"' in preview
    assert '"content":"[redacted]"' in preview
    assert '"customerEmail":"[redacted]"' in preview
    assert '"safe":"visible"' in preview


def test_body_preview_truncates_large_payloads() -> None:
    preview = body_preview({"safe": "x" * 2_000})

    assert preview is not None
    assert len(preview.encode("utf-8")) <= 1_040
    assert preview.endswith("...[truncated]")


@pytest.mark.asyncio
async def test_request_retries_idempotent_get_and_logs_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture_logger = CaptureLogger()
    monkeypatch.setattr(outbound_http, "logger", capture_logger)
    responses = [
        httpx.Response(503, json={"error": {"message": "busy"}}),
        httpx.Response(200, json={"id": "cs_test_observed"}),
    ]

    def respond(_: httpx.Request) -> httpx.Response:
        return responses.pop(0)

    with respx.mock:
        route = respx.get("https://stripe.example/v1/checkout/sessions/cs_test_observed").mock(
            side_effect=respond
        )

        response = await request(
            provider="stripe",
            method="GET",
            url="https://stripe.example/v1/checkout/sessions/cs_test_observed",
            timeout_seconds=1,
            retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0, jitter_seconds=0),
        )

    assert response.status_code == 200
    assert len(route.calls) == 2
    finished_events = [
        kwargs
        for event, kwargs in capture_logger.events
        if event == "outbound_http_request_finished"
    ]
    assert finished_events[0]["status_code"] == 503
    assert finished_events[0]["retrying"] is True
    assert finished_events[1]["status_code"] == 200
    assert finished_events[1]["retrying"] is False


@pytest.mark.asyncio
async def test_request_does_not_retry_non_idempotent_post_and_redacts_logs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture_logger = CaptureLogger()
    monkeypatch.setattr(outbound_http, "logger", capture_logger)

    with respx.mock:
        route = respx.post("https://api.example.test/send").mock(
            return_value=httpx.Response(503, json={"error": {"message": "busy"}})
        )

        response = await request(
            provider="sendgrid",
            method="POST",
            url="https://api.example.test/send",
            timeout_seconds=1,
            json_body={"content": "private email body", "safe": "visible"},
            request_body_for_logs={"content": "private email body", "safe": "visible"},
            retry_policy=RetryPolicy(max_attempts=3, base_delay_seconds=0, jitter_seconds=0),
        )

    assert response.status_code == 503
    assert len(route.calls) == 1
    started = next(
        kwargs
        for event, kwargs in capture_logger.events
        if event == "outbound_http_request_started"
    )
    assert started["request_body"] == '{"content":"[redacted]","safe":"visible"}'


@pytest.mark.asyncio
async def test_stream_lines_logs_completion_without_buffering_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture_logger = CaptureLogger()
    monkeypatch.setattr(outbound_http, "logger", capture_logger)

    with respx.mock:
        route = respx.post("https://openai.example/v1/chat/completions").mock(
            return_value=httpx.Response(200, text="data: one\n\ndata: [DONE]\n")
        )

        lines = [
            line
            async for line in stream_lines(
                provider="openai",
                method="POST",
                url="https://openai.example/v1/chat/completions",
                timeout_seconds=1,
                json_body={"messages": [{"content": "private prompt"}], "stream": True},
                request_body_for_logs={"messages": [{"content": "private prompt"}], "stream": True},
            )
        ]

    assert lines == ["data: one", "", "data: [DONE]"]
    assert len(route.calls) == 1
    finished = next(
        kwargs
        for event, kwargs in capture_logger.events
        if event == "outbound_http_request_finished"
    )
    assert finished["status_code"] == 200
    assert finished["response_body"] is None
    assert finished["stream_lines"] == 3

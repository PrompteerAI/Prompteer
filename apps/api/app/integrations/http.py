# Shared outbound HTTP helpers for real upstream integration clients.
# Adds structured observability and conservative retry behavior without a new dependency.

from __future__ import annotations

import asyncio
import json
import random
import time
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast

import httpx
import structlog

MAX_LOG_BODY_BYTES = 1024
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
RETRYABLE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
SENSITIVE_LOG_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "client_secret",
        "content",
        "customer_email",
        "email",
        "from",
        "id_token",
        "key",
        "password",
        "refresh_token",
        "secret",
        "text",
        "to",
        "token",
        "value",
    }
)


class OutboundLogger(Protocol):
    def info(self, event: str, **kwargs: Any) -> Any: ...

    def warning(self, event: str, **kwargs: Any) -> Any: ...


logger = cast(OutboundLogger, structlog.get_logger(__name__))


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.2
    jitter_seconds: float = 0.05
    retryable_status_codes: frozenset[int] = RETRYABLE_STATUS_CODES
    retryable_methods: frozenset[str] = RETRYABLE_METHODS


async def request(
    *,
    provider: str,
    method: str,
    url: str,
    timeout_seconds: float,
    headers: Mapping[str, str] | None = None,
    json_body: object | None = None,
    content: str | bytes | None = None,
    request_body_for_logs: object | None = None,
    retry_policy: RetryPolicy | None = None,
) -> httpx.Response:
    """Send one upstream request with structured logs and opt-in idempotent retries."""
    normalized_method = method.upper()
    attempts = _attempt_count(normalized_method, retry_policy)
    request_preview = body_preview(
        request_body_for_logs if request_body_for_logs is not None else json_body or content
    )

    last_error: httpx.TransportError | None = None
    for attempt in range(1, attempts + 1):
        logger.info(
            "outbound_http_request_started",
            provider=provider,
            method=normalized_method,
            host=_url_host(url),
            path=_url_path(url),
            attempt=attempt,
            max_attempts=attempts,
            request_body=request_preview,
        )
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.request(
                    normalized_method,
                    url,
                    headers=dict(headers or {}),
                    json=json_body,
                    content=content,
                )
        except httpx.TransportError as exc:
            last_error = exc
            retrying = attempt < attempts
            logger.warning(
                "outbound_http_request_failed",
                provider=provider,
                method=normalized_method,
                host=_url_host(url),
                path=_url_path(url),
                attempt=attempt,
                max_attempts=attempts,
                duration_ms=_elapsed_ms(started),
                error_type=type(exc).__name__,
                retrying=retrying,
            )
            if retrying:
                await _sleep_before_retry(attempt, retry_policy)
                continue
            raise

        duration_ms = _elapsed_ms(started)
        retrying = _should_retry_response(
            response,
            normalized_method,
            attempt,
            attempts,
            retry_policy,
        )
        logger.info(
            "outbound_http_request_finished",
            provider=provider,
            method=normalized_method,
            host=_url_host(url),
            path=_url_path(url),
            attempt=attempt,
            max_attempts=attempts,
            duration_ms=duration_ms,
            status_code=response.status_code,
            response_body=body_preview(response_body_for_logs(response)),
            retrying=retrying,
        )
        if retrying:
            await _sleep_before_retry(attempt, retry_policy)
            continue
        return response

    if last_error is not None:
        raise last_error
    raise RuntimeError("Outbound HTTP request exhausted attempts without a response.")


async def stream_lines(
    *,
    provider: str,
    method: str,
    url: str,
    timeout_seconds: float,
    headers: Mapping[str, str] | None = None,
    json_body: object | None = None,
    request_body_for_logs: object | None = None,
) -> AsyncIterator[str]:
    """Stream an upstream response while logging start/end metadata."""
    normalized_method = method.upper()
    request_preview = body_preview(
        request_body_for_logs if request_body_for_logs is not None else json_body
    )
    logger.info(
        "outbound_http_request_started",
        provider=provider,
        method=normalized_method,
        host=_url_host(url),
        path=_url_path(url),
        attempt=1,
        max_attempts=1,
        request_body=request_preview,
    )
    started = time.perf_counter()
    status_code: int | None = None
    line_count = 0
    transport_failed = False
    try:
        async with (
            httpx.AsyncClient(timeout=timeout_seconds) as client,
            client.stream(
                normalized_method,
                url,
                headers=dict(headers or {}),
                json=json_body,
            ) as response,
        ):
            status_code = response.status_code
            response.raise_for_status()
            async for line in response.aiter_lines():
                line_count += 1
                yield line
    except httpx.TransportError as exc:
        transport_failed = True
        logger.warning(
            "outbound_http_request_failed",
            provider=provider,
            method=normalized_method,
            host=_url_host(url),
            path=_url_path(url),
            attempt=1,
            max_attempts=1,
            duration_ms=_elapsed_ms(started),
            error_type=type(exc).__name__,
            retrying=False,
        )
        raise
    finally:
        if not transport_failed:
            logger.info(
                "outbound_http_request_finished",
                provider=provider,
                method=normalized_method,
                host=_url_host(url),
                path=_url_path(url),
                attempt=1,
                max_attempts=1,
                duration_ms=_elapsed_ms(started),
                status_code=status_code,
                response_body=None,
                retrying=False,
                stream_lines=line_count,
            )


def body_preview(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        raw = value.decode("utf-8", errors="replace")
    elif isinstance(value, str):
        raw = value
    else:
        raw = json.dumps(_redact(value), default=str, sort_keys=True, separators=(",", ":"))
    return _truncate_utf8(raw, MAX_LOG_BODY_BYTES)


def response_body_for_logs(response: httpx.Response) -> object | None:
    if not response.content:
        return None
    text = response.text
    try:
        return cast(object, json.loads(text))
    except json.JSONDecodeError:
        return text


def _attempt_count(method: str, retry_policy: RetryPolicy | None) -> int:
    if retry_policy is None or method not in retry_policy.retryable_methods:
        return 1
    return max(1, retry_policy.max_attempts)


def _should_retry_response(
    response: httpx.Response,
    method: str,
    attempt: int,
    max_attempts: int,
    retry_policy: RetryPolicy | None,
) -> bool:
    if retry_policy is None or method not in retry_policy.retryable_methods:
        return False
    return response.status_code in retry_policy.retryable_status_codes and attempt < max_attempts


async def _sleep_before_retry(attempt: int, retry_policy: RetryPolicy | None) -> None:
    if retry_policy is None:
        return
    base_delay = retry_policy.base_delay_seconds * (2 ** (attempt - 1))
    jitter = random.uniform(0, retry_policy.jitter_seconds) if retry_policy.jitter_seconds else 0
    await asyncio.sleep(base_delay + jitter)


def _redact(value: object) -> object:
    if isinstance(value, Mapping):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in SENSITIVE_LOG_KEYS:
                redacted[key_text] = "[redacted]"
            else:
                redacted[key_text] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
        return [_redact(item) for item in value]
    return value


def _truncate_utf8(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "...[truncated]"


def _elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def _url_host(url: str) -> str:
    return httpx.URL(url).host or ""


def _url_path(url: str) -> str:
    parsed = httpx.URL(url)
    return parsed.path or "/"

"""SlowAPI limiter setup and keying policy for user-scoped request throttles."""

from functools import lru_cache
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from math import ceil
from time import time

from limits import parse as parse_rate_limit
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette import status
from starlette.requests import Request

from app.core.config import settings
from app.core.errors import ProblemException
from app.core.security import Principal


def rate_limit_key(request: Request) -> str:
    principal = getattr(request.state, "principal", None)
    if isinstance(principal, Principal):
        return f"user:{principal.subject}"
    return f"ip:{rate_limit_ip(request)}"


def rate_limit_ip(request: Request) -> str:
    remote_address = get_remote_address(request)
    if is_trusted_proxy(remote_address):
        forwarded_address = forwarded_for_address(request)
        if forwarded_address is not None:
            return forwarded_address
    return remote_address


def forwarded_for_address(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if not forwarded_for:
        return None
    valid_hops = [
        candidate.strip()
        for candidate in forwarded_for.split(",")
        if is_valid_ip_address(candidate.strip())
    ]
    for candidate in reversed(valid_hops):
        if not is_trusted_proxy(candidate):
            return candidate
    return None


def is_trusted_proxy(address: str) -> bool:
    try:
        parsed_address = ip_address(address)
    except ValueError:
        return False
    return any(parsed_address in network for network in trusted_proxy_networks())


@lru_cache
def trusted_proxy_networks() -> tuple[IPv4Network | IPv6Network, ...]:
    networks = []
    for raw_network in settings.rate_limit_trusted_proxy_cidrs.split(","):
        raw_network = raw_network.strip()
        if not raw_network:
            continue
        networks.append(ip_network(raw_network, strict=False))
    return tuple(networks)


def is_valid_ip_address(address: str) -> bool:
    try:
        ip_address(address)
    except ValueError:
        return False
    return True


def enforce_auth_attempt_rate_limit(request: Request) -> None:
    """Throttle auth dependency work before JWT/JWKS validation can spend resources."""
    if not limiter.enabled:
        return
    limit = parse_rate_limit(settings.auth_attempt_rate_limit)
    key = f"auth:{rate_limit_ip(request)}"
    allowed = limiter.limiter.hit(limit, key)
    if allowed:
        return
    window = limiter.limiter.get_window_stats(limit, key)
    retry_after = max(1, ceil(window.reset_time - time()))
    raise ProblemException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        title="Too Many Requests",
        detail="Too many authentication attempts. Wait a moment, then try again.",
        code="rate_limited",
        headers={"Retry-After": str(retry_after)},
    )


limiter = Limiter(
    key_func=rate_limit_key,
    enabled=settings.rate_limit_enabled,
    headers_enabled=settings.rate_limit_headers_enabled,
    in_memory_fallback_enabled=False,
    key_prefix=settings.rate_limit_key_prefix,
    retry_after="delta-seconds",
    storage_uri=settings.rate_limit_storage_url,
    strategy=settings.rate_limit_strategy,
)

GENERAL_RATE_LIMIT = settings.general_rate_limit
AUTH_ATTEMPT_RATE_LIMIT = settings.auth_attempt_rate_limit
LLM_RATE_LIMIT = settings.llm_rate_limit
PAYMENTS_RATE_LIMIT = settings.payments_rate_limit
STRIPE_WEBHOOK_RATE_LIMIT = settings.stripe_webhook_rate_limit
EMAIL_RATE_LIMIT = settings.email_rate_limit

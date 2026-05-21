"""SlowAPI limiter setup and keying policy for user-scoped request throttles."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings
from app.core.security import Principal


def rate_limit_key(request: Request) -> str:
    principal = getattr(request.state, "principal", None)
    if isinstance(principal, Principal):
        return f"user:{principal.subject}"
    return f"ip:{get_remote_address(request)}"


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
LLM_RATE_LIMIT = settings.llm_rate_limit
PAYMENTS_RATE_LIMIT = settings.payments_rate_limit
EMAIL_RATE_LIMIT = settings.email_rate_limit

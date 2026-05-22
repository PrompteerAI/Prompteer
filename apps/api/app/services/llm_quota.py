"""Daily per-user LLM token quota accounting and enforcement."""

from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session

from app.core.config import settings
from app.core.errors import ProblemException
from app.core.security import Principal
from app.models.domain import LLMUsageDay, User
from app.repositories import llm_usage as llm_usage_repository
from app.repositories import users as users_repository


def resolve_user_for_principal(session: Session, principal: Principal) -> User:
    user = users_repository.get_user_by_auth_subject(session, principal.subject)
    if user is None:
        user = users_repository.get_user_by_id(session, principal.subject)
    principal_email = normalized_email(principal.email) if principal.email else None
    if user is None and principal_email:
        user = users_repository.get_user_by_email(session, principal_email)
    if user is not None:
        return user

    if not principal_email:
        raise ProblemException(
            status_code=401,
            title="Unauthorized",
            detail="Authenticated prompt runs require an email claim.",
            code="missing_email_claim",
        )

    user = User(
        auth_subject=principal.subject,
        email=principal_email,
        display_name=principal_email.split("@", maxsplit=1)[0],
    )
    return users_repository.add_user(session, user)


def normalized_email(email: str) -> str:
    return email.strip().lower()


def assert_llm_quota_available(
    session: Session,
    user: User,
    *,
    requested_tokens: int = 0,
) -> None:
    cap = daily_token_cap(user)
    if cap is None:
        return

    usage = llm_usage_repository.get_usage_day(
        session,
        user_id=user.id,
        usage_day=current_usage_date(),
    )
    used_tokens = usage.total_tokens if usage is not None else 0
    projected_tokens = used_tokens + max(0, requested_tokens)
    if used_tokens >= cap or projected_tokens > cap:
        raise quota_exceeded(user=user, cap=cap, used=max(used_tokens, projected_tokens))


def record_llm_usage(
    session: Session,
    user: User,
    usage: dict[str, Any],
    *,
    commit: bool = True,
) -> LLMUsageDay:
    usage_day = current_usage_date()
    prompt_tokens = non_negative_int(usage.get("prompt_tokens"))
    completion_tokens = non_negative_int(usage.get("completion_tokens"))
    total_tokens = non_negative_int(usage.get("total_tokens"))
    cap = daily_token_cap(user)
    if cap is not None and total_tokens > cap:
        raise quota_exceeded(user=user, cap=cap, used=total_tokens)

    usage_row = llm_usage_repository.increment_usage_day(
        session,
        user=user,
        usage_day=usage_day,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cap=cap,
    )
    if usage_row is None:
        existing = llm_usage_repository.get_usage_day(
            session,
            user_id=user.id,
            usage_day=usage_day,
        )
        used = (existing.total_tokens if existing is not None else 0) + total_tokens
        session.rollback()
        raise quota_exceeded(user=user, cap=cap or 0, used=used)

    if commit:
        session.commit()
    else:
        session.flush()
    refreshed = llm_usage_repository.get_usage_day(
        session,
        user_id=user.id,
        usage_day=usage_day,
    )
    if refreshed is None:
        raise RuntimeError("LLM usage row disappeared after quota update.")
    return refreshed


def daily_token_cap(user: User) -> int | None:
    if user.role == "admin":
        return None
    if user.plan == "paid":
        return settings.llm_paid_daily_token_cap
    return settings.llm_free_daily_token_cap


def current_usage_date() -> date:
    return datetime.now(tz=UTC).date()


def quota_exceeded(*, user: User, cap: int, used: int) -> ProblemException:
    return ProblemException(
        status_code=402,
        title="LLM quota exceeded",
        detail=(
            f"{user.email} has used {used:,} of {cap:,} daily LLM tokens. "
            "Wait until tomorrow or upgrade the account."
        ),
        code="quota_exceeded",
    )


def non_negative_int(value: Any) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 0

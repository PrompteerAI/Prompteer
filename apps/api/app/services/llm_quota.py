from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session, select

from app.core.config import settings
from app.core.errors import ProblemException
from app.core.security import Principal
from app.models.domain import LLMUsageDay, User, utc_now


def resolve_user_for_principal(session: Session, principal: Principal) -> User:
    user = session.exec(select(User).where(User.auth_subject == principal.subject)).first()
    if user is None:
        user = session.get(User, principal.subject)
    if user is None and principal.email:
        user = session.exec(select(User).where(User.email == principal.email)).first()
    if user is not None:
        return user

    if not principal.email:
        raise ProblemException(
            status_code=401,
            title="Unauthorized",
            detail="Authenticated prompt runs require an email claim.",
            code="missing_email_claim",
        )

    user = User(
        auth_subject=principal.subject,
        email=principal.email,
        display_name=principal.email.split("@", maxsplit=1)[0],
    )
    session.add(user)
    session.flush()
    return user


def assert_llm_quota_available(session: Session, user: User) -> None:
    cap = daily_token_cap(user)
    if cap is None:
        return

    usage = session.get(LLMUsageDay, (user.id, current_usage_date()))
    if usage is not None and usage.total_tokens >= cap:
        raise quota_exceeded(user=user, cap=cap, used=usage.total_tokens)


def record_llm_usage(session: Session, user: User, usage: dict[str, Any]) -> LLMUsageDay:
    usage_day = current_usage_date()
    usage_row = session.get(LLMUsageDay, (user.id, usage_day))
    if usage_row is None:
        usage_row = LLMUsageDay(user_id=user.id, usage_date=usage_day)

    prompt_tokens = non_negative_int(usage.get("prompt_tokens"))
    completion_tokens = non_negative_int(usage.get("completion_tokens"))
    total_tokens = non_negative_int(usage.get("total_tokens"))

    usage_row.prompt_tokens += prompt_tokens
    usage_row.completion_tokens += completion_tokens
    usage_row.total_tokens += total_tokens
    usage_row.request_count += 1
    usage_row.updated_at = utc_now()
    session.add(usage_row)
    session.commit()
    session.refresh(usage_row)

    cap = daily_token_cap(user)
    if cap is not None and usage_row.total_tokens > cap:
        raise quota_exceeded(user=user, cap=cap, used=usage_row.total_tokens)

    return usage_row


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

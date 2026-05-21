"""Daily per-user LLM token quota accounting and enforcement."""

from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select

from app.core.config import settings
from app.core.errors import ProblemException
from app.core.security import Principal
from app.models.domain import LLMUsageDay, User, utc_now


def resolve_user_for_principal(session: Session, principal: Principal) -> User:
    user = session.exec(select(User).where(User.auth_subject == principal.subject)).first()
    if user is None:
        user = session.get(User, principal.subject)
    principal_email = normalized_email(principal.email) if principal.email else None
    if user is None and principal_email:
        user = session.exec(select(User).where(User.email == principal_email)).first()
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
    session.add(user)
    session.flush()
    return user


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

    usage = session.get(LLMUsageDay, (user.id, current_usage_date()))
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

    usage_row = upsert_llm_usage_day(
        session,
        user=user,
        usage_day=usage_day,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cap=cap,
    )
    if usage_row is None:
        existing = session.get(LLMUsageDay, (user.id, usage_day))
        used = (existing.total_tokens if existing is not None else 0) + total_tokens
        session.rollback()
        raise quota_exceeded(user=user, cap=cap or 0, used=used)

    if commit:
        session.commit()
    else:
        session.flush()
    refreshed = session.get(LLMUsageDay, (user.id, usage_day))
    if refreshed is None:
        raise RuntimeError("LLM usage row disappeared after quota update.")
    return refreshed


def upsert_llm_usage_day(
    session: Session,
    *,
    user: User,
    usage_day: date,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cap: int | None,
) -> LLMUsageDay | None:
    dialect_name = session.get_bind().dialect.name
    if dialect_name not in {"postgresql", "sqlite"}:
        return locked_record_llm_usage(
            session,
            user=user,
            usage_day=usage_day,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cap=cap,
        )

    table: Any = cast(Any, LLMUsageDay).__table__
    now = utc_now()
    if dialect_name == "postgresql":
        statement: Any = postgresql_insert(table).values(
            user_id=user.id,
            usage_date=usage_day,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            request_count=1,
            updated_at=now,
        )
    else:
        statement = sqlite_insert(table).values(
            user_id=user.id,
            usage_date=usage_day,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            request_count=1,
            updated_at=now,
        )
    update_values = {
        "prompt_tokens": table.c.prompt_tokens + prompt_tokens,
        "completion_tokens": table.c.completion_tokens + completion_tokens,
        "total_tokens": table.c.total_tokens + total_tokens,
        "request_count": table.c.request_count + 1,
        "updated_at": now,
    }
    conflict_options: dict[str, Any] = {
        "index_elements": [table.c.user_id, table.c.usage_date],
        "set_": update_values,
    }
    if cap is not None:
        conflict_options["where"] = table.c.total_tokens + total_tokens <= cap
    statement = statement.on_conflict_do_update(**conflict_options).returning(
        table.c.user_id,
        table.c.usage_date,
    )
    row = session.execute(statement).first()
    if row is None:
        return None
    return session.get(LLMUsageDay, (user.id, usage_day))


def locked_record_llm_usage(
    session: Session,
    *,
    user: User,
    usage_day: date,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cap: int | None,
) -> LLMUsageDay | None:
    usage_row = session.exec(
        select(LLMUsageDay)
        .where(LLMUsageDay.user_id == user.id, LLMUsageDay.usage_date == usage_day)
        .with_for_update()
    ).first()
    if usage_row is None:
        usage_row = LLMUsageDay(user_id=user.id, usage_date=usage_day)
    projected_total_tokens = usage_row.total_tokens + total_tokens
    if cap is not None and projected_total_tokens > cap:
        return None
    usage_row.prompt_tokens += prompt_tokens
    usage_row.completion_tokens += completion_tokens
    usage_row.total_tokens = projected_total_tokens
    usage_row.request_count += 1
    usage_row.updated_at = utc_now()
    session.add(usage_row)
    session.flush()
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

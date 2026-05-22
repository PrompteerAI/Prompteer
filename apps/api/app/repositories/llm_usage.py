"""Persistence helpers for daily LLM quota accounting."""

from datetime import date
from typing import Any, cast

from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select

from app.models.domain import LLMUsageDay, User, utc_now


def get_usage_day(
    session: Session,
    *,
    user_id: str,
    usage_day: date,
) -> LLMUsageDay | None:
    return session.get(LLMUsageDay, (user_id, usage_day))


def increment_usage_day(
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
        return locked_increment_usage_day(
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
    insert_values = {
        "user_id": user.id,
        "usage_date": usage_day,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "request_count": 1,
        "updated_at": now,
    }
    if dialect_name == "postgresql":
        statement: Any = postgresql_insert(table).values(**insert_values)
    else:
        statement = sqlite_insert(table).values(**insert_values)
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
    return get_usage_day(session, user_id=user.id, usage_day=usage_day)


def locked_increment_usage_day(
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

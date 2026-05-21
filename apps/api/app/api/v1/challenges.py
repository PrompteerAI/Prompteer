"""API v1 challenge routes; no sibling challenge API version exists yet."""

from collections import defaultdict
from collections.abc import Iterable
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, col, select

from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.errors import ProblemException
from app.core.feature_flags import require_feature_enabled
from app.core.ratelimit import GENERAL_RATE_LIMIT, LLM_RATE_LIMIT, limiter
from app.core.security import Principal
from app.core.time import ensure_utc
from app.db.session import get_session
from app.integrations.llm import get_llm_client
from app.integrations.llm.base import LLMClient, LLMProviderError
from app.models.domain import (
    Challenge,
    ChallengeTag,
    ImgReference,
    Share,
    VideoReference,
    utc_now,
)
from app.schemas.challenge import (
    ChallengeRead,
    ChallengeReferenceRead,
    ChallengeRunRequest,
    ChallengeRunResponse,
    ChallengeRunShareRead,
    ImgChallengeReferenceRead,
    VideoChallengeReferenceRead,
)
from app.services.llm_quota import (
    assert_llm_quota_available,
    record_llm_usage,
    resolve_user_for_principal,
)

router = APIRouter(prefix="/challenges", tags=["challenges"])

MOCK_CHAT_MODEL = "mock-gpt-4.1-mini"
ANTHROPIC_MAX_TOKENS = 512
SYSTEM_PROMPT = (
    "You are evaluating a Prompteer challenge submission. "
    "Respond with concise feedback and a stronger prompt."
)


@router.get("")
@limiter.limit(GENERAL_RATE_LIMIT)
async def list_challenges(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    tag: Annotated[ChallengeTag | None, Query()] = None,
) -> list[ChallengeRead]:
    del request, response
    statement = select(Challenge).order_by(col(Challenge.challenge_number))
    if tag is not None:
        statement = statement.where(Challenge.tag == tag)
    challenges = list(session.exec(statement).all())
    references_by_challenge_id = load_challenge_references(session, challenges)
    return [
        challenge_to_read(
            challenge,
            references=references_by_challenge_id.get(challenge.id, []),
        )
        for challenge in challenges
    ]


@router.get("/{challenge_id}")
@limiter.limit(GENERAL_RATE_LIMIT)
async def get_challenge(
    request: Request,
    response: Response,
    challenge_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ChallengeRead:
    del request, response
    challenge = load_challenge(session, challenge_id)
    references_by_challenge_id = load_challenge_references(session, [challenge])
    return challenge_to_read(
        challenge,
        references=references_by_challenge_id.get(challenge.id, []),
    )


@router.post("/{challenge_id}/run")
@limiter.limit(LLM_RATE_LIMIT)
async def run_challenge_prompt(
    request: Request,
    response: Response,
    challenge_id: str,
    run_request: ChallengeRunRequest,
    session: Annotated[Session, Depends(get_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ChallengeRunResponse:
    del request, response
    require_feature_enabled("llm")
    challenge = load_challenge(session, challenge_id)
    user = resolve_user_for_principal(session, principal)
    assert_llm_quota_available(
        session,
        user,
        requested_tokens=estimated_prompt_run_tokens(
            challenge=challenge,
            prompt=run_request.prompt,
        ),
    )
    llm_client = get_llm_client()
    try:
        llm_result = await run_feedback_prompt(
            llm_client,
            challenge=challenge,
            prompt=run_request.prompt,
        )
    except LLMProviderError as exc:
        raise ProblemException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            title="LLM Provider Error",
            detail=exc.detail,
            code="llm_provider_error",
        ) from exc
    try:
        record_llm_usage(session, user, llm_result["usage"], commit=False)
        share = create_prompt_share(
            session,
            user_id=user.id,
            challenge_id=challenge.id,
            run=run_request,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    if share is not None:
        session.refresh(share)
    references = load_challenge_references(session, [challenge]).get(challenge.id, [])
    return ChallengeRunResponse(
        challenge=challenge_to_read(
            challenge,
            references=references,
        ),
        prompt=run_request.prompt,
        provider=llm_client.provider,
        output=llm_result["output"],
        usage=llm_result["usage"],
        share=share_to_run_read(share) if share is not None else None,
    )


async def run_feedback_prompt(
    llm_client: LLMClient,
    *,
    challenge: Challenge,
    prompt: str,
) -> dict[str, Any]:
    user_content = challenge_prompt_content(challenge=challenge, prompt=prompt)
    if llm_client.provider == "anthropic":
        response = await llm_client.anthropic_message(
            {
                "model": settings.anthropic_model,
                "max_tokens": ANTHROPIC_MAX_TOKENS,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_content}],
            }
        )
        return {
            "output": extract_anthropic_text(response),
            "usage": normalize_anthropic_usage(response.get("usage")),
        }

    response = await llm_client.chat_completion(
        {
            "model": chat_model_for_provider(llm_client.provider),
            "max_completion_tokens": settings.openai_max_completion_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }
    )
    return {
        "output": extract_openai_text(response),
        "usage": normalize_openai_usage(response.get("usage")),
    }


def challenge_prompt_content(*, challenge: Challenge, prompt: str) -> str:
    return (
        f"Challenge: {challenge.title}\n"
        f"Instructions: {challenge.content or 'No extra instructions.'}\n"
        f"Submitted prompt: {prompt}"
    )


def estimated_prompt_run_tokens(*, challenge: Challenge, prompt: str) -> int:
    prompt_budget = estimate_text_tokens(
        SYSTEM_PROMPT,
        challenge.title,
        challenge.content or "",
        prompt,
    )
    return prompt_budget + max(settings.openai_max_completion_tokens, ANTHROPIC_MAX_TOKENS)


def estimate_text_tokens(*parts: str) -> int:
    character_count = sum(len(part) for part in parts)
    return max(1, (character_count + 3) // 4)


def chat_model_for_provider(provider: str) -> str:
    if provider == "openai":
        return settings.openai_chat_model
    return MOCK_CHAT_MODEL


def extract_openai_text(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""
    message = first_choice.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def extract_anthropic_text(response: dict[str, Any]) -> str:
    content = response.get("content")
    if not isinstance(content, list):
        return ""
    parts = [
        block["text"]
        for block in content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    ]
    return "\n".join(parts)


def normalize_openai_usage(usage: Any) -> dict[str, int]:
    if not isinstance(usage, dict):
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    prompt_tokens = non_negative_int(usage.get("prompt_tokens"))
    completion_tokens = non_negative_int(usage.get("completion_tokens"))
    total_tokens = non_negative_int(usage.get("total_tokens"))
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def normalize_anthropic_usage(usage: Any) -> dict[str, int]:
    if not isinstance(usage, dict):
        input_tokens = 0
        output_tokens = 0
    else:
        input_tokens = non_negative_int(usage.get("input_tokens"))
        output_tokens = non_negative_int(usage.get("output_tokens"))
    return {
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def non_negative_int(value: Any) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 0


def load_challenge(session: Session, challenge_id: str) -> Challenge:
    challenge = session.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found.",
        )
    return challenge


def load_challenge_references(
    session: Session,
    challenges: Iterable[Challenge],
) -> dict[str, list[ChallengeReferenceRead]]:
    challenge_ids_by_tag: dict[ChallengeTag, list[str]] = defaultdict(list)
    for challenge in challenges:
        challenge_ids_by_tag[challenge.tag].append(challenge.id)

    references_by_challenge_id: dict[str, list[ChallengeReferenceRead]] = defaultdict(list)
    img_challenge_ids = challenge_ids_by_tag[ChallengeTag.img]
    if img_challenge_ids:
        img_references = session.exec(
            select(ImgReference)
            .where(col(ImgReference.challenge_id).in_(img_challenge_ids))
            .order_by(
                col(ImgReference.challenge_id),
                col(ImgReference.file_path),
                col(ImgReference.id),
            )
        ).all()
        for img_reference in img_references:
            references_by_challenge_id[img_reference.challenge_id].append(
                ImgChallengeReferenceRead(
                    kind="img",
                    id=img_reference.id,
                    file_path=img_reference.file_path,
                    file_type=img_reference.file_type,
                )
            )

    video_challenge_ids = challenge_ids_by_tag[ChallengeTag.video]
    if video_challenge_ids:
        video_references = session.exec(
            select(VideoReference)
            .where(col(VideoReference.challenge_id).in_(video_challenge_ids))
            .order_by(
                col(VideoReference.challenge_id),
                col(VideoReference.file_path),
                col(VideoReference.id),
            )
        ).all()
        for video_reference in video_references:
            references_by_challenge_id[video_reference.challenge_id].append(
                VideoChallengeReferenceRead(
                    kind="video",
                    id=video_reference.id,
                    file_path=video_reference.file_path,
                    file_type=video_reference.file_type,
                )
            )

    return dict(references_by_challenge_id)


def challenge_to_read(
    challenge: Challenge,
    *,
    references: list[ChallengeReferenceRead],
) -> ChallengeRead:
    return ChallengeRead(
        id=challenge.id,
        challenge_number=challenge.challenge_number,
        tag=challenge.tag,
        level=challenge.level,
        title=challenge.title,
        content=challenge.content,
        references=references,
    )


def create_prompt_share(
    session: Session,
    *,
    user_id: str,
    challenge_id: str,
    run: ChallengeRunRequest,
) -> Share | None:
    if not run.publish_to_board:
        return None
    share = upsert_prompt_share(
        session,
        user_id=user_id,
        challenge_id=challenge_id,
        prompt=run.prompt,
    )
    session.flush()
    return share


def upsert_prompt_share(
    session: Session,
    *,
    user_id: str,
    challenge_id: str,
    prompt: str,
) -> Share:
    dialect_name = session.get_bind().dialect.name
    if dialect_name in {"postgresql", "sqlite"}:
        return dialect_upsert_prompt_share(
            session,
            dialect_name=dialect_name,
            user_id=user_id,
            challenge_id=challenge_id,
            prompt=prompt,
        )

    share = session.exec(
        select(Share)
        .where(Share.user_id == user_id, Share.challenge_id == challenge_id)
        .with_for_update()
        .order_by(col(Share.updated_at).desc(), col(Share.created_at).desc())
    ).first()
    if share is None:
        share = Share(
            challenge_id=challenge_id,
            user_id=user_id,
            prompt=prompt,
            is_public=True,
        )
    else:
        share.prompt = prompt
        share.is_public = True
        share.updated_at = utc_now()
    session.add(share)
    session.flush()
    return share


def dialect_upsert_prompt_share(
    session: Session,
    *,
    dialect_name: str,
    user_id: str,
    challenge_id: str,
    prompt: str,
) -> Share:
    table: Any = cast(Any, Share).__table__
    now = utc_now()
    insert_values = {
        "challenge_id": challenge_id,
        "user_id": user_id,
        "prompt": prompt,
        "is_public": True,
        "created_at": now,
        "updated_at": now,
    }
    if dialect_name == "postgresql":
        statement: Any = postgresql_insert(table).values(**insert_values)
    else:
        statement = sqlite_insert(table).values(**insert_values)
    statement = statement.on_conflict_do_update(
        index_elements=[table.c.user_id, table.c.challenge_id],
        set_={
            "prompt": prompt,
            "is_public": True,
            "updated_at": now,
        },
    ).returning(table.c.id)
    row = session.execute(statement).first()
    if row is None:
        raise RuntimeError("Prompt share upsert did not return a row.")
    share = session.get(Share, row[0])
    if share is None:
        raise RuntimeError("Prompt share row disappeared after upsert.")
    return share


def share_to_run_read(share: Share) -> ChallengeRunShareRead:
    return ChallengeRunShareRead(
        id=share.id,
        is_public=share.is_public,
        created_at=ensure_utc(share.created_at),
    )

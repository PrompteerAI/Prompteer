"""API v1 challenge routes; no sibling challenge API version exists yet."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session, col, select

from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.feature_flags import require_feature_enabled
from app.core.ratelimit import GENERAL_RATE_LIMIT, LLM_RATE_LIMIT, limiter
from app.core.security import Principal
from app.core.time import ensure_utc
from app.db.session import get_session
from app.integrations.llm import get_llm_client
from app.integrations.llm.base import LLMClient
from app.models.domain import Challenge, ChallengeTag, Share, utc_now
from app.schemas.challenge import (
    ChallengeRead,
    ChallengeRunRequest,
    ChallengeRunResponse,
    ChallengeRunShareRead,
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
    return [challenge_to_read(challenge) for challenge in session.exec(statement).all()]


@router.get("/{challenge_id}")
@limiter.limit(GENERAL_RATE_LIMIT)
async def get_challenge(
    request: Request,
    response: Response,
    challenge_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ChallengeRead:
    del request, response
    return challenge_to_read(load_challenge(session, challenge_id))


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
    assert_llm_quota_available(session, user)
    llm_client = get_llm_client()
    llm_result = await run_feedback_prompt(
        llm_client,
        challenge=challenge,
        prompt=run_request.prompt,
    )
    record_llm_usage(session, user, llm_result["usage"])
    share = create_prompt_share(
        session,
        user_id=user.id,
        challenge_id=challenge.id,
        run=run_request,
    )
    return ChallengeRunResponse(
        challenge=challenge_to_read(challenge),
        prompt=run_request.prompt,
        provider=llm_client.provider,
        output=llm_result["output"],
        usage=llm_result["usage"],
        raw=llm_result["raw"],
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
            "raw": response,
        }

    response = await llm_client.chat_completion(
        {
            "model": chat_model_for_provider(llm_client.provider),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }
    )
    return {
        "output": extract_openai_text(response),
        "usage": normalize_openai_usage(response.get("usage")),
        "raw": response,
    }


def challenge_prompt_content(*, challenge: Challenge, prompt: str) -> str:
    return (
        f"Challenge: {challenge.title}\n"
        f"Instructions: {challenge.content or 'No extra instructions.'}\n"
        f"Submitted prompt: {prompt}"
    )


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


def challenge_to_read(challenge: Challenge) -> ChallengeRead:
    return ChallengeRead(
        id=challenge.id,
        challenge_number=challenge.challenge_number,
        tag=challenge.tag,
        level=challenge.level,
        title=challenge.title,
        content=challenge.content,
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
    share = session.exec(
        select(Share)
        .where(Share.user_id == user_id, Share.challenge_id == challenge_id)
        .order_by(col(Share.updated_at).desc(), col(Share.created_at).desc())
    ).first()
    if share is None:
        share = Share(
            challenge_id=challenge_id,
            user_id=user_id,
            prompt=run.prompt,
            is_public=True,
        )
    else:
        share.prompt = run.prompt
        share.is_public = True
        share.updated_at = utc_now()
    session.add(share)
    session.commit()
    session.refresh(share)
    return share


def share_to_run_read(share: Share) -> ChallengeRunShareRead:
    return ChallengeRunShareRead(
        id=share.id,
        is_public=share.is_public,
        created_at=ensure_utc(share.created_at),
    )

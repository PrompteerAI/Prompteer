"""Challenge services that coordinate reads, LLM feedback, quotas, and sharing."""

from typing import Any

from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.config import settings
from app.core.errors import ProblemException
from app.core.feature_flags import require_feature_enabled
from app.core.security import Principal
from app.core.time import ensure_utc
from app.integrations.llm import get_llm_client
from app.integrations.llm.base import LLMClient, LLMProviderError
from app.models.domain import Challenge, ChallengeTag, ImgReference, Share, VideoReference
from app.repositories import challenges as challenge_repository
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

MOCK_CHAT_MODEL = "mock-gpt-4.1-mini"
ANTHROPIC_MAX_TOKENS = 512
SYSTEM_PROMPT = (
    "You are evaluating a Prompteer challenge submission. "
    "Respond with concise feedback and a stronger prompt."
)


def list_challenge_reads(
    session: Session,
    *,
    tag: ChallengeTag | None,
) -> list[ChallengeRead]:
    challenges = challenge_repository.list_challenges(session, tag=tag)
    references_by_challenge_id = load_challenge_references(session, challenges)
    return [
        challenge_to_read(
            challenge,
            references=references_by_challenge_id.get(challenge.id, []),
        )
        for challenge in challenges
    ]


def get_challenge_read(session: Session, challenge_id: str) -> ChallengeRead:
    challenge = load_challenge(session, challenge_id)
    references_by_challenge_id = load_challenge_references(session, [challenge])
    return challenge_to_read(
        challenge,
        references=references_by_challenge_id.get(challenge.id, []),
    )


async def run_challenge_prompt(
    session: Session,
    *,
    challenge_id: str,
    run_request: ChallengeRunRequest,
    principal: Principal,
) -> ChallengeRunResponse:
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
        share_read = share_to_run_read(share) if share is not None else None
        session.commit()
    except Exception:
        session.rollback()
        raise

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
        share=share_read,
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
    challenge = challenge_repository.get_challenge(session, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found.",
        )
    return challenge


def load_challenge_references(
    session: Session,
    challenges: list[Challenge],
) -> dict[str, list[ChallengeReferenceRead]]:
    references = challenge_repository.load_challenge_references(session, challenges)
    return {
        challenge_id: [reference_to_read(reference) for reference in reference_records]
        for challenge_id, reference_records in references.items()
    }


def reference_to_read(
    reference: challenge_repository.ChallengeReferenceRecord,
) -> ChallengeReferenceRead:
    if isinstance(reference, ImgReference):
        return ImgChallengeReferenceRead(
            kind="img",
            id=reference.id,
            file_path=reference.file_path,
            file_type=reference.file_type,
        )
    if isinstance(reference, VideoReference):
        return VideoChallengeReferenceRead(
            kind="video",
            id=reference.id,
            file_path=reference.file_path,
            file_type=reference.file_type,
        )
    raise TypeError(f"Unsupported challenge reference: {type(reference).__name__}")


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
    share = challenge_repository.upsert_prompt_share(
        session,
        user_id=user_id,
        challenge_id=challenge_id,
        prompt=run.prompt,
    )
    return share


def share_to_run_read(share: Share) -> ChallengeRunShareRead:
    return ChallengeRunShareRead(
        id=share.id,
        is_public=share.is_public,
        created_at=ensure_utc(share.created_at),
    )

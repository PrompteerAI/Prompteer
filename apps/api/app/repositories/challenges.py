"""Persistence helpers for challenge reads, references, and prompt shares."""

from collections import defaultdict
from collections.abc import Iterable
from typing import Any, cast

from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, col, select

from app.models.domain import (
    Challenge,
    ChallengeTag,
    ImgReference,
    Share,
    VideoReference,
    utc_now,
)

ChallengeReferenceRecord = ImgReference | VideoReference


def list_challenges(
    session: Session,
    *,
    tag: ChallengeTag | None = None,
) -> list[Challenge]:
    statement = select(Challenge).order_by(col(Challenge.challenge_number))
    if tag is not None:
        statement = statement.where(Challenge.tag == tag)
    return list(session.exec(statement).all())


def get_challenge(session: Session, challenge_id: str) -> Challenge | None:
    return session.get(Challenge, challenge_id)


def load_challenge_references(
    session: Session,
    challenges: Iterable[Challenge],
) -> dict[str, list[ChallengeReferenceRecord]]:
    challenge_ids_by_tag: dict[ChallengeTag, list[str]] = defaultdict(list)
    for challenge in challenges:
        challenge_ids_by_tag[challenge.tag].append(challenge.id)

    references_by_challenge_id: dict[str, list[ChallengeReferenceRecord]] = defaultdict(list)
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
            references_by_challenge_id[img_reference.challenge_id].append(img_reference)

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
            references_by_challenge_id[video_reference.challenge_id].append(video_reference)

    return dict(references_by_challenge_id)


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

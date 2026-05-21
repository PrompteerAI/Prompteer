"""Idempotent demo data and mock email seed routines for local development."""

from datetime import UTC, datetime, timedelta

from alembic import command
from sqlmodel import Session, select

from app.core.config import settings
from app.core.migrations import alembic_config
from app.db.session import engine
from app.integrations.email.mock import MockSendGridClient
from app.integrations.payments.mock import seed_completed_checkout_session
from app.models.domain import (
    Challenge,
    ChallengeLevel,
    ChallengeTag,
    ImgChallenge,
    ImgReference,
    Post,
    PostType,
    Profile,
    PSChallenge,
    PSTestcase,
    Share,
    User,
    VideoChallenge,
    VideoReference,
)
from app.services.billing import record_checkout_session

DEMO_USERS = {
    "admin@prompteer.dev": {
        "id": "00000000-0000-4000-8000-000000000001",
        "auth_subject": "mock-google-oauth2|admin",
        "display_name": "Prompteer Admin",
        "role": "admin",
        "plan": "paid",
    },
    "paid@prompteer.dev": {
        "id": "00000000-0000-4000-8000-000000000002",
        "auth_subject": "mock-google-oauth2|paid",
        "display_name": "Paid Prompt Engineer",
        "role": "user",
        "plan": "paid",
    },
    "free@prompteer.dev": {
        "id": "00000000-0000-4000-8000-000000000003",
        "auth_subject": "mock-google-oauth2|free",
        "display_name": "Free Prompt Builder",
        "role": "user",
        "plan": "free",
    },
}

DEMO_CONTENT_CREATED_AT = datetime(2026, 5, 21, 9, 0, tzinfo=UTC)


def seed(session: Session) -> None:
    users_by_email = seed_users(session)
    seed_mock_checkouts(session, users_by_email)
    seed_challenges(session, users_by_email)
    session.commit()


def seed_users(session: Session) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, data in DEMO_USERS.items():
        user = session.exec(select(User).where(User.email == email)).one_or_none()
        if user is None:
            user = User(email=email, **data)
            session.add(user)
            session.flush()
        ensure_profile(session, user=user, email=email, display_name=str(data["display_name"]))
        users[email] = user
    return users


def ensure_profile(session: Session, *, user: User, email: str, display_name: str) -> None:
    profile = session.get(Profile, user.id)
    introduction = f"Demo account for {display_name}."
    interests = {"prompt_engineer": True, "ps": email == "free@prompteer.dev"}
    if profile is None:
        session.add(
            Profile(
                user_id=user.id,
                introduction=introduction,
                interests=interests,
            )
        )
        return

    profile.introduction = introduction
    profile.interests = interests
    session.add(profile)


def seed_mock_checkouts(session: Session, users_by_email: dict[str, User]) -> None:
    for email, data in DEMO_USERS.items():
        if data["plan"] != "paid":
            continue
        result = seed_completed_checkout_session(
            {
                "mode": "subscription",
                "success_url": f"{settings.app_url}/en/billing/success",
                "cancel_url": f"{settings.app_url}/en/billing",
                "customer_email": email,
                "metadata": {
                    "plan": "pro",
                    "user_id": users_by_email[email].id,
                    "seed_user_id": users_by_email[email].id,
                },
                "line_items": [
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": 1200,
                            "recurring": {"interval": "month"},
                            "product_data": {"name": "Prompteer Pro"},
                        },
                    }
                ],
            },
            seed_key=email,
        )
        record_checkout_session(
            session,
            result["session"],
            user=users_by_email[email],
            provider="mock",
            plan="pro",
        )


def seed_challenges(session: Session, users_by_email: dict[str, User]) -> None:
    admin = users_by_email["admin@prompteer.dev"]
    paid_user = users_by_email["paid@prompteer.dev"]
    free_user = users_by_email["free@prompteer.dev"]
    challenge_specs = [
        (
            1,
            ChallengeTag.ps,
            ChallengeLevel.easy,
            "FizzBuzz prompt repair",
            (
                "Write a prompt that makes an assistant explain the FizzBuzz rules, "
                "handle divisibility by 3 and 5 correctly, and produce concise Python "
                "with edge cases for small inputs."
            ),
        ),
        (
            2,
            ChallengeTag.img,
            ChallengeLevel.medium,
            "Product hero image prompt",
            (
                "Create a product hero image prompt for a compact AI note-taking device. "
                "The output should specify lighting, materials, background, camera angle, "
                "and what must remain readable."
            ),
        ),
        (
            3,
            ChallengeTag.video,
            ChallengeLevel.hard,
            "Launch teaser video prompt",
            (
                "Draft a short launch teaser prompt with scene beats, pacing, transitions, "
                "and soundtrack direction for a developer productivity tool."
            ),
        ),
        (
            4,
            ChallengeTag.ps,
            ChallengeLevel.medium,
            "Stable sorting explanation",
            (
                "Repair a coding prompt so the assistant explains stable sorting, chooses "
                "an appropriate algorithm, and includes a Python example that preserves "
                "original order for equal keys."
            ),
        ),
        (
            5,
            ChallengeTag.ps,
            ChallengeLevel.hard,
            "Graph traversal guardrails",
            (
                "Design a prompt that asks for BFS and DFS tradeoffs, disconnected graph "
                "handling, cycle safety, and complexity analysis before writing code."
            ),
        ),
    ]
    for number, tag, level, title, content in challenge_specs:
        challenge = session.exec(
            select(Challenge).where(Challenge.challenge_number == number)
        ).one_or_none()
        if challenge is None:
            challenge = Challenge(
                owner_id=admin.id,
                tag=tag,
                level=level,
                title=title,
                content=content,
                challenge_number=number,
            )
            session.add(challenge)
            session.flush()
        else:
            challenge.owner_id = admin.id
            challenge.tag = tag
            challenge.level = level
            challenge.title = title
            challenge.content = content
            session.add(challenge)
            session.flush()
        ensure_type_specific_challenge(session, challenge)

    challenge_1 = session.exec(select(Challenge).where(Challenge.challenge_number == 1)).one()
    challenge_4 = session.exec(select(Challenge).where(Challenge.challenge_number == 4)).one()
    challenge_5 = session.exec(select(Challenge).where(Challenge.challenge_number == 5)).one()
    ensure_share(
        session,
        user=free_user,
        challenge=challenge_1,
        prompt="Explain the FizzBuzz rules first, then produce concise Python.",
        created_at=DEMO_CONTENT_CREATED_AT,
    )
    ensure_share(
        session,
        user=paid_user,
        challenge=challenge_4,
        prompt="Show why stable sorting matters before giving a compact Python example.",
        created_at=DEMO_CONTENT_CREATED_AT + timedelta(minutes=10),
    )
    ensure_share(
        session,
        user=admin,
        challenge=challenge_5,
        prompt="Compare BFS and DFS, then solve disconnected graph traversal safely.",
        created_at=DEMO_CONTENT_CREATED_AT + timedelta(minutes=20),
    )
    ensure_post(
        session,
        user=free_user,
        challenge=challenge_1,
        title="How should I structure PS prompts?",
        content="I am comparing prompts that ask for reasoning before code.",
        post_type=PostType.question,
        created_at=DEMO_CONTENT_CREATED_AT + timedelta(minutes=1),
    )
    ensure_post(
        session,
        user=paid_user,
        challenge=challenge_4,
        title="Stable sort prompts that avoid over-explaining",
        content="The best runs asked for invariants, examples, and a short implementation.",
        post_type=PostType.share,
        created_at=DEMO_CONTENT_CREATED_AT + timedelta(minutes=11),
    )
    ensure_post(
        session,
        user=admin,
        challenge=challenge_5,
        title="Graph traversal guardrails for prompt reviews",
        content="Cycle safety and disconnected components should be explicit in the prompt.",
        post_type=PostType.question,
        created_at=DEMO_CONTENT_CREATED_AT + timedelta(minutes=21),
    )


def ensure_share(
    session: Session,
    *,
    user: User,
    challenge: Challenge,
    prompt: str,
    created_at: datetime,
) -> None:
    share = session.exec(
        select(Share).where(Share.user_id == user.id, Share.challenge_id == challenge.id)
    ).one_or_none()
    if share is None:
        session.add(
            Share(
                user_id=user.id,
                challenge_id=challenge.id,
                prompt=prompt,
                is_public=True,
                created_at=created_at,
                updated_at=created_at,
            )
        )
    else:
        share.prompt = prompt
        share.is_public = True
        share.created_at = created_at
        share.updated_at = created_at
        session.add(share)


def ensure_post(
    session: Session,
    *,
    user: User,
    challenge: Challenge,
    title: str,
    content: str,
    post_type: PostType,
    created_at: datetime,
) -> None:
    post = session.exec(select(Post).where(Post.title == title)).one_or_none()
    if post is None:
        session.add(
            Post(
                user_id=user.id,
                challenge_id=challenge.id,
                type=post_type,
                tag=challenge.tag,
                title=title,
                content=content,
                created_at=created_at,
                updated_at=created_at,
            )
        )
    else:
        post.user_id = user.id
        post.challenge_id = challenge.id
        post.type = post_type
        post.tag = challenge.tag
        post.content = content
        post.created_at = created_at
        post.updated_at = created_at
        session.add(post)


def ensure_type_specific_challenge(session: Session, challenge: Challenge) -> None:
    if challenge.tag == ChallengeTag.ps:
        if session.get(PSChallenge, challenge.id) is None:
            session.add(PSChallenge(challenge_id=challenge.id))
        testcase = session.exec(
            select(PSTestcase).where(PSTestcase.challenge_id == challenge.id)
        ).first()
        if testcase is None:
            session.add(PSTestcase(challenge_id=challenge.id, input="15", output="FizzBuzz"))
    elif challenge.tag == ChallengeTag.img:
        if session.get(ImgChallenge, challenge.id) is None:
            session.add(ImgChallenge(challenge_id=challenge.id))
        img_reference = session.exec(
            select(ImgReference).where(ImgReference.challenge_id == challenge.id)
        ).first()
        if img_reference is None:
            session.add(
                ImgReference(
                    challenge_id=challenge.id,
                    file_path="seed/references/product-hero.png",
                    file_type="image/png",
                )
            )
    elif challenge.tag == ChallengeTag.video:
        if session.get(VideoChallenge, challenge.id) is None:
            session.add(VideoChallenge(challenge_id=challenge.id))
        video_reference = session.exec(
            select(VideoReference).where(VideoReference.challenge_id == challenge.id)
        ).first()
        if video_reference is None:
            session.add(
                VideoReference(
                    challenge_id=challenge.id,
                    file_path="seed/references/launch-teaser.mp4",
                    file_type="video/mp4",
                )
            )


def main() -> None:
    command.upgrade(alembic_config(), "head")
    with Session(engine) as session:
        seed(session)
    seed_mock_emails()
    print("Seeded Prompteer demo data.")


def seed_mock_emails() -> None:
    client = MockSendGridClient()
    payloads = [
        (
            "seed-welcome-admin",
            {
                "personalizations": [{"to": [{"email": "admin@prompteer.dev"}]}],
                "from": {"email": settings.sendgrid_from_email},
                "subject": "Prompteer admin workspace is ready",
                "content": [
                    {
                        "type": "text/plain",
                        "value": "The local Prompteer admin account has been seeded.",
                    }
                ],
            },
        ),
        (
            "seed-subscription-paid",
            {
                "personalizations": [{"to": [{"email": "paid@prompteer.dev"}]}],
                "from": {"email": settings.sendgrid_from_email},
                "subject": "Mock subscription receipt",
                "content": [
                    {
                        "type": "text/plain",
                        "value": (
                            "A mock paid subscription checkout has completed for this account."
                        ),
                    }
                ],
            },
        ),
        (
            "seed-challenge-free",
            {
                "personalizations": [{"to": [{"email": "free@prompteer.dev"}]}],
                "from": {"email": settings.sendgrid_from_email},
                "subject": "Your first prompt challenge is waiting",
                "content": [
                    {
                        "type": "text/html",
                        "value": "<p>Try the seeded FizzBuzz prompt repair challenge.</p>",
                    }
                ],
            },
        ),
    ]
    for filename_prefix, payload in payloads:
        client.capture_payload(payload, filename_prefix=filename_prefix, overwrite=False)


if __name__ == "__main__":
    main()

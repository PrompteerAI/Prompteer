from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import settings
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


def seed(session: Session) -> None:
    users_by_email = seed_users(session)
    seed_challenges(session, users_by_email)
    session.commit()


def seed_users(session: Session) -> dict[str, User]:
    users: dict[str, User] = {}
    for email, data in DEMO_USERS.items():
        user = session.exec(select(User).where(User.email == email)).one_or_none()
        if user is None:
            user = User(email=email, **data)
            session.add(user)
            session.add(
                Profile(
                    user_id=user.id,
                    introduction=f"Demo account for {data['display_name']}.",
                    interests={"prompt_engineer": True, "ps": email == "free@prompteer.dev"},
                )
            )
        users[email] = user
    return users


def seed_challenges(session: Session, users_by_email: dict[str, User]) -> None:
    admin = users_by_email["admin@prompteer.dev"]
    free_user = users_by_email["free@prompteer.dev"]
    challenge_specs = [
        (1, ChallengeTag.ps, ChallengeLevel.easy, "FizzBuzz prompt repair"),
        (2, ChallengeTag.img, ChallengeLevel.medium, "Product hero image prompt"),
        (3, ChallengeTag.video, ChallengeLevel.hard, "Launch teaser video prompt"),
    ]
    for number, tag, level, title in challenge_specs:
        challenge = session.exec(
            select(Challenge).where(Challenge.challenge_number == number)
        ).one_or_none()
        if challenge is None:
            challenge = Challenge(
                owner_id=admin.id,
                tag=tag,
                level=level,
                title=title,
                content=f"Demo {tag.value} challenge for local development.",
                challenge_number=number,
            )
            session.add(challenge)
            session.flush()
            add_type_specific_challenge(session, challenge)

    first_challenge = session.exec(select(Challenge).where(Challenge.challenge_number == 1)).one()
    share = session.exec(
        select(Share).where(Share.user_id == free_user.id, Share.challenge_id == first_challenge.id)
    ).one_or_none()
    if share is None:
        session.add(
            Share(
                user_id=free_user.id,
                challenge_id=first_challenge.id,
                prompt="Explain the FizzBuzz rules first, then produce concise Python.",
                is_public=True,
            )
        )
    post = session.exec(
        select(Post).where(Post.title == "How should I structure PS prompts?")
    ).one_or_none()
    if post is None:
        session.add(
            Post(
                user_id=free_user.id,
                challenge_id=first_challenge.id,
                type=PostType.question,
                tag=ChallengeTag.ps,
                title="How should I structure PS prompts?",
                content="I am comparing prompts that ask for reasoning before code.",
            )
        )


def add_type_specific_challenge(session: Session, challenge: Challenge) -> None:
    if challenge.tag == ChallengeTag.ps:
        session.add(PSChallenge(challenge_id=challenge.id))
        session.add(PSTestcase(challenge_id=challenge.id, input="15", output="FizzBuzz"))
    elif challenge.tag == ChallengeTag.img:
        session.add(ImgChallenge(challenge_id=challenge.id))
        session.add(
            ImgReference(
                challenge_id=challenge.id,
                file_path="seed/references/product-hero.png",
                file_type="image/png",
            )
        )
    elif challenge.tag == ChallengeTag.video:
        session.add(VideoChallenge(challenge_id=challenge.id))
        session.add(
            VideoReference(
                challenge_id=challenge.id,
                file_path="seed/references/launch-teaser.mp4",
                file_type="video/mp4",
            )
        )


def main() -> None:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)
    print("Seeded Prompteer demo data.")


if __name__ == "__main__":
    main()

from app.core.security import Principal


async def get_current_principal() -> Principal:
    return Principal(subject="dev-user", email="free@prompteer.dev")

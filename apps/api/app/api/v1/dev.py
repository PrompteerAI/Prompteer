"""API v1 development-only routes; no sibling dev API version exists yet."""

from fastapi import APIRouter, HTTPException

from app.core.feature_flags import dev_routes_enabled
from app.integrations.email.mock import MockSendGridClient

router = APIRouter(prefix="/dev", tags=["dev"])


def require_dev_routes() -> None:
    if not dev_routes_enabled():
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/mailbox")
async def mailbox() -> dict[str, object]:
    require_dev_routes()
    client = MockSendGridClient()
    return {"messages": client.list_messages()}


@router.get("/mailbox/{message_id}")
async def mailbox_message(message_id: str) -> dict[str, str]:
    require_dev_routes()
    client = MockSendGridClient()
    try:
        return client.read_message(message_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Message not found") from exc

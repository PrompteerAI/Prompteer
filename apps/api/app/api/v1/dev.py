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

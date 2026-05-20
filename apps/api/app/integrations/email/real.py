from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class SendGridClient:
    api_key: str
    base_url: str = "https://api.sendgrid.com"
    timeout_seconds: float = 15.0
    provider: str = "sendgrid"

    async def send(self, payload: dict[str, Any]) -> dict[str, str]:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url.rstrip('/')}/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        return {"status": "accepted", "captured": "0"}

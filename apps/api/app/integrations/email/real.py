# Real SendGrid Mail Send client used when SENDGRID_API_KEY is configured.
# Delivery remains one-shot to avoid duplicate emails on ambiguous upstream failures.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.integrations.http import request


@dataclass(frozen=True)
class SendGridClient:
    api_key: str
    base_url: str = "https://api.sendgrid.com"
    timeout_seconds: float = 15.0
    provider: str = "sendgrid"

    async def send(self, payload: dict[str, Any]) -> dict[str, str]:
        response = await request(
            provider=self.provider,
            method="POST",
            url=f"{self.base_url.rstrip('/')}/v3/mail/send",
            timeout_seconds=self.timeout_seconds,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json_body=payload,
            request_body_for_logs=payload,
        )
        response.raise_for_status()
        return {"status": "accepted", "captured": "0"}

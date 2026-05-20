"""SendGrid mail send mock.

Schema reference verified on 2026-05-20:
- https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send
"""

from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from re import sub
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class EmailAddress(BaseModel):
    email: EmailStr
    name: str | None = None


class Personalization(BaseModel):
    to: list[EmailAddress] = Field(min_length=1)
    dynamic_template_data: dict[str, Any] | None = None


class ContentBlock(BaseModel):
    type: str
    value: str


class SendGridMailPayload(BaseModel):
    personalizations: list[Personalization] = Field(min_length=1)
    from_: EmailAddress = Field(alias="from")
    subject: str = Field(min_length=1)
    content: list[ContentBlock] = Field(default_factory=list)
    template_id: str | None = None


class MockSendGridClient:
    def __init__(self, mailbox_dir: Path | str = ".mock/email") -> None:
        self.mailbox_dir = Path(mailbox_dir)

    async def send(self, payload: dict[str, Any]) -> dict[str, str]:
        message = SendGridMailPayload.model_validate(payload)
        self.mailbox_dir.mkdir(parents=True, exist_ok=True)

        written_to: list[str] = []
        for personalization in message.personalizations:
            for recipient in personalization.to:
                path = self.mailbox_dir / self._filename(recipient.email)
                path.write_text(self._to_eml(message, recipient), encoding="utf-8")
                written_to.append(str(path))

        return {"status": "accepted", "captured": str(len(written_to))}

    def list_messages(self) -> list[dict[str, str]]:
        if not self.mailbox_dir.exists():
            return []
        return [
            {"id": path.name, "path": str(path)}
            for path in sorted(self.mailbox_dir.glob("*.eml"), reverse=True)
        ]

    @staticmethod
    def _filename(email: str) -> str:
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        safe_to = sub(r"[^a-zA-Z0-9_.@-]+", "_", email)
        return f"{timestamp}-{safe_to}.eml"

    @staticmethod
    def _to_eml(message: SendGridMailPayload, recipient: EmailAddress) -> str:
        email = EmailMessage()
        email["To"] = recipient.email
        email["From"] = message.from_.email
        email["Subject"] = message.subject

        plain = next(
            (block.value for block in message.content if block.type == "text/plain"),
            None,
        )
        html = next(
            (block.value for block in message.content if block.type == "text/html"),
            None,
        )

        if plain is not None:
            email.set_content(plain)
        elif html is not None:
            email.set_content("HTML email captured by Prompteer mock mailbox.")
        else:
            email.set_content("Template email captured by Prompteer mock mailbox.")

        if html is not None:
            email.add_alternative(html, subtype="html")

        return email.as_string()

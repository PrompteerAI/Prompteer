"""SendGrid mail send mock.

Schema reference verified on 2026-05-22:
- https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send
- https://www.twilio.com/docs/sendgrid/api-reference/mail-send/errors
"""

import json
from datetime import UTC, datetime
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from re import sub
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator, model_validator
from starlette import status
from starlette.responses import Response

from app.core.config import integration_modes, settings
from app.core.errors import ProblemException
from app.core.feature_flags import dev_routes_enabled, require_feature_enabled
from app.core.ratelimit import EMAIL_RATE_LIMIT, limiter

router = APIRouter(tags=["mock-sendgrid"])
logger = structlog.get_logger(__name__)


def default_mailbox_dir() -> Path:
    if settings.mock_mailbox_dir:
        return Path(settings.mock_mailbox_dir)
    return Path(__file__).resolve().parents[5] / ".mock" / "email"


class EmailAddress(BaseModel):
    email: EmailStr
    name: str | None = None


class Personalization(BaseModel):
    to: list[EmailAddress] = Field(min_length=1)
    cc: list[EmailAddress] = Field(default_factory=list)
    bcc: list[EmailAddress] = Field(default_factory=list)
    subject: str | None = Field(default=None, min_length=1)
    dynamic_template_data: dict[str, Any] | None = None


class ContentBlock(BaseModel):
    type: str
    value: str = Field(min_length=1)

    @field_validator("type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        if value not in {"text/plain", "text/html"}:
            raise ValueError("content type must be text/plain or text/html")
        return value


class SendGridMailPayload(BaseModel):
    personalizations: list[Personalization] = Field(min_length=1)
    from_: EmailAddress = Field(alias="from")
    subject: str | None = Field(default=None, min_length=1)
    content: list[ContentBlock] = Field(default_factory=list)
    template_id: str | None = None

    @model_validator(mode="after")
    def validate_sendgrid_requirements(self) -> "SendGridMailPayload":
        has_template = bool(self.template_id)
        if not has_template and not self.content:
            raise ValueError("content is required unless template_id is provided")
        has_subject = (
            bool(self.subject)
            or has_template
            or all(personalization.subject for personalization in self.personalizations)
        )
        if not has_subject:
            raise ValueError(
                "subject is required unless template_id is provided "
                "or every personalization has a subject"
            )
        return self


def require_mock_routes() -> bool:
    if integration_modes()["email"] != "mock":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not dev_routes_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return True


@router.post("/v3/mail/send", response_model=None)
@limiter.limit(EMAIL_RATE_LIMIT)
async def sendgrid_mail_send(
    request: Request,
    response: Response,
    payload: dict[str, Any],
) -> Response:
    del request, response
    require_mock_routes()
    require_feature_enabled("email")
    client = MockSendGridClient()
    try:
        await client.send(payload)
    except ValidationError as exc:
        raise ProblemException(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Bad Request",
            detail="The SendGrid mail send payload is invalid.",
            code="sendgrid_payload_invalid",
            errors=sendgrid_validation_errors(exc),
        ) from exc
    return Response(status_code=status.HTTP_202_ACCEPTED)


class MockSendGridClient:
    provider = "mock"

    def __init__(self, mailbox_dir: Path | str | None = None) -> None:
        self.mailbox_dir = Path(mailbox_dir) if mailbox_dir is not None else default_mailbox_dir()

    async def send(self, payload: dict[str, Any]) -> dict[str, str]:
        written_to = self.capture_payload(payload)
        return {"status": "accepted", "captured": str(len(written_to))}

    def capture_payload(
        self,
        payload: dict[str, Any],
        *,
        filename_prefix: str | None = None,
        overwrite: bool = True,
    ) -> list[Path]:
        message = SendGridMailPayload.model_validate(payload)
        self.mailbox_dir.mkdir(parents=True, exist_ok=True)

        written_to: list[Path] = []
        for personalization in message.personalizations:
            for recipient in personalization.to:
                path = self.mailbox_dir / self._filename(recipient.email, prefix=filename_prefix)
                if overwrite or not path.exists():
                    path.write_text(
                        self._to_eml(message, personalization, recipient),
                        encoding="utf-8",
                    )
                    log_fields = {
                        "recipient": recipient.email,
                        "capture_path": str(path),
                    }
                    subject = personalization.subject or message.subject
                    if subject is not None:
                        log_fields["subject"] = subject
                    logger.info("mock_email_captured", **log_fields)
                written_to.append(path)

        return written_to

    def list_messages(self) -> list[dict[str, str]]:
        if not self.mailbox_dir.exists():
            return []
        return [
            self._summary(path) for path in sorted(self.mailbox_dir.glob("*.eml"), reverse=True)
        ]

    def read_message(self, message_id: str) -> dict[str, str]:
        path = self._message_path(message_id)
        summary = self._summary(path)
        return {**summary, "raw": path.read_text(encoding="utf-8")}

    @staticmethod
    def _filename(email: str, *, prefix: str | None = None) -> str:
        timestamp = prefix or datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
        safe_to = sub(r"[^a-zA-Z0-9_.@-]+", "_", email)
        return f"{timestamp}-{safe_to}.eml"

    @staticmethod
    def _to_eml(
        message: SendGridMailPayload,
        personalization: Personalization,
        recipient: EmailAddress,
    ) -> str:
        email = EmailMessage()
        email["To"] = recipient.email
        email["From"] = message.from_.email
        email["Subject"] = (
            personalization.subject or message.subject or "SendGrid dynamic template email"
        )
        if message.template_id is not None:
            email["X-SendGrid-Template-Id"] = message.template_id

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
            body = "Template email captured by Prompteer mock mailbox."
            if personalization.dynamic_template_data is not None:
                body += "\n\nDynamic template data:\n" + json_dump_template_data(
                    personalization.dynamic_template_data
                )
            email.set_content(body)

        if html is not None:
            email.add_alternative(html, subtype="html")

        return email.as_string()

    def _message_path(self, message_id: str) -> Path:
        if Path(message_id).name != message_id or not message_id.endswith(".eml"):
            raise FileNotFoundError(message_id)
        path = self.mailbox_dir / message_id
        if not path.is_file():
            raise FileNotFoundError(message_id)
        return path

    @staticmethod
    def _summary(path: Path) -> dict[str, str]:
        message = BytesParser(policy=default).parsebytes(path.read_bytes())
        return {
            "id": path.name,
            "path": str(path),
            "to": str(message.get("to", "")),
            "from": str(message.get("from", "")),
            "subject": str(message.get("subject", "")),
        }


def sendgrid_validation_errors(exc: ValidationError) -> list[dict[str, str | None]]:
    return [
        {
            "message": str(error["msg"]),
            "field": ".".join(str(part) for part in error["loc"]),
            "help": None,
        }
        for error in exc.errors()
    ]


def json_dump_template_data(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)

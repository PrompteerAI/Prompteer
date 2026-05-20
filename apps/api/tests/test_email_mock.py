from pathlib import Path

import pytest

from app.integrations.email.mock import MockSendGridClient


@pytest.mark.asyncio
async def test_mock_sendgrid_captures_eml(tmp_path: Path) -> None:
    client = MockSendGridClient(mailbox_dir=tmp_path)

    result = await client.send(
        {
            "personalizations": [{"to": [{"email": "free@prompteer.dev"}]}],
            "from": {"email": "no-reply@prompteer.dev"},
            "subject": "Welcome to Prompteer",
            "content": [{"type": "text/plain", "value": "Hello from the mock mailbox."}],
        }
    )

    messages = client.list_messages()
    assert result == {"status": "accepted", "captured": "1"}
    assert len(messages) == 1
    assert Path(messages[0]["path"]).read_text(encoding="utf-8").count("Welcome to Prompteer") == 1

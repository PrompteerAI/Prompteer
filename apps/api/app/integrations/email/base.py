from typing import Any, Protocol


class EmailClient(Protocol):
    @property
    def provider(self) -> str:
        """The selected email provider name for boot logs and diagnostics."""

    async def send(self, payload: dict[str, Any]) -> dict[str, str]:
        """Send a SendGrid Mail Send compatible payload."""

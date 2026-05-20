"""Shared integration protocols for provider clients used by the API."""

from typing import Protocol


class IntegrationStatus(Protocol):
    name: str
    mode: str

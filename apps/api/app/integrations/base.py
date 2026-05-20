from typing import Protocol


class IntegrationStatus(Protocol):
    name: str
    mode: str

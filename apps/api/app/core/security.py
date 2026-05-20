from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None = None
    is_admin: bool = False

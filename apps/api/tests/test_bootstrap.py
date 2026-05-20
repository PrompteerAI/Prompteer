from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, select

from app.core import bootstrap
from app.core.config import settings
from app.core.migrations import migration_state
from app.integrations.email import mock as email_mock
from app.models.domain import Post, Share, User


def test_development_bootstrap_runs_migrations_and_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'bootstrap.db'}"
    engine = create_engine(database_url, pool_pre_ping=True)
    mailbox_dir = tmp_path / ".mock" / "email"

    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "auto_seed_on_startup", True)
    monkeypatch.setattr(settings, "database_url", database_url)
    monkeypatch.setattr(bootstrap, "engine", engine)
    monkeypatch.setattr(email_mock, "default_mailbox_dir", lambda: mailbox_dir)

    bootstrap.run_development_bootstrap()
    bootstrap.run_development_bootstrap()

    migrations = migration_state(engine)
    assert migrations.status == "ok"
    assert migrations.current == migrations.head
    with Session(engine) as session:
        assert len(session.exec(select(User)).all()) == 3
        assert len(session.exec(select(Share)).all()) == 3
        assert len(session.exec(select(Post)).all()) == 3
    assert sorted(path.name for path in mailbox_dir.glob("seed-*.eml")) == [
        "seed-challenge-free-free@prompteer.dev.eml",
        "seed-subscription-paid-paid@prompteer.dev.eml",
        "seed-welcome-admin-admin@prompteer.dev.eml",
    ]

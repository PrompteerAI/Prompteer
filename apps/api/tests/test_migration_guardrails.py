"""Tests for Alembic destructive migration guardrails."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check-migration-guardrails.py"


def load_guardrail_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_guardrails", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_migration(path: Path, body: str) -> Path:
    path.write_text(
        f'''
"""temporary test migration"""

from alembic import op

{body}
'''.lstrip(),
        encoding="utf-8",
    )
    return path


def test_destructive_upgrade_requires_adr(tmp_path: Path) -> None:
    guardrails = load_guardrail_module()
    migration = write_migration(
        tmp_path / "drop_table.py",
        """
def upgrade() -> None:
    op.drop_table("legacy_table")
""",
    )

    failures = guardrails.check_migration(migration)

    assert len(failures) == 1
    assert "destructive upgrade operations without" in failures[0]
    assert "op.drop_table" in failures[0]


def test_destructive_helper_call_requires_adr(tmp_path: Path) -> None:
    guardrails = load_guardrail_module()
    migration = write_migration(
        tmp_path / "alter_column.py",
        """
def upgrade() -> None:
    convert_column()


def convert_column() -> None:
    op.alter_column("users", "created_at", type_=object())
""",
    )

    failures = guardrails.check_migration(migration)

    assert len(failures) == 1
    assert "op.alter_column(type_=...)" in failures[0]


def test_acknowledged_destructive_upgrade_passes(tmp_path: Path) -> None:
    guardrails = load_guardrail_module()
    migration = write_migration(
        tmp_path / "acknowledged_delete.py",
        """
destructive_migration_adr = "docs/adr/0022-share-uniqueness-migration.md"


def upgrade() -> None:
    op.execute("DELETE FROM shares")
""",
    )

    assert guardrails.check_migration(migration) == []

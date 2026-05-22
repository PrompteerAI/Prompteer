"""Fail Alembic upgrades that contain destructive operations without an ADR."""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DIR = REPO_ROOT / "apps" / "api" / "app" / "alembic" / "versions"
ACK_NAME = "destructive_migration_adr"

RISKY_OP_METHODS = {
    "drop_column": "drops a column",
    "drop_constraint": "drops a constraint",
    "drop_table": "drops a table",
}

RISKY_SQL_PATTERNS = (
    (re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE), "deletes data"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "truncates data"),
    (
        re.compile(r"\bDROP\s+(TABLE|COLUMN|TYPE|CONSTRAINT)\b", re.IGNORECASE),
        "drops schema",
    ),
    (
        re.compile(r"\bALTER\s+TABLE\b.*\bDROP\b", re.IGNORECASE | re.DOTALL),
        "drops schema through ALTER TABLE",
    ),
    (
        re.compile(r"\bALTER\s+TABLE\b.*\bTYPE\b", re.IGNORECASE | re.DOTALL),
        "changes a column type through ALTER TABLE",
    ),
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    detail: str

    def display(self) -> str:
        return f"{display_path(self.path)}:{self.line}: {self.detail}"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def module_ack(tree: ast.Module) -> str | None:
    for statement in tree.body:
        target_name: str | None = None
        value: ast.expr | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                target_name = target.id
                value = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(
            statement.target, ast.Name
        ):
            target_name = statement.target.id
            value = statement.value

        if (
            target_name == ACK_NAME
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            return value.value

    return None


def functions_by_name(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, ast.FunctionDef)
    }


def alembic_op_method(call: ast.Call) -> str | None:
    if not isinstance(call.func, ast.Attribute):
        return None
    if not isinstance(call.func.value, ast.Name):
        return None
    if call.func.value.id not in {"op", "batch_op"}:
        return None
    return call.func.attr


def literal_sql(call: ast.Call) -> str | None:
    if len(call.args) != 1:
        return None

    arg = call.args[0]
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return arg.value

    if (
        isinstance(arg, ast.Call)
        and isinstance(arg.func, ast.Attribute)
        and isinstance(arg.func.value, ast.Name)
        and arg.func.value.id == "sa"
        and arg.func.attr == "text"
        and len(arg.args) == 1
        and isinstance(arg.args[0], ast.Constant)
        and isinstance(arg.args[0].value, str)
    ):
        return arg.args[0].value

    return None


def call_risk(call: ast.Call) -> str | None:
    method = alembic_op_method(call)
    if method in RISKY_OP_METHODS:
        return f"upgrade {RISKY_OP_METHODS[method]} via op.{method}()"
    if method == "alter_column" and any(
        keyword.arg == "type_" for keyword in call.keywords
    ):
        return "upgrade changes a column type via op.alter_column(type_=...)"
    if method == "execute":
        sql = literal_sql(call)
        if sql is None:
            return None
        for pattern, description in RISKY_SQL_PATTERNS:
            if pattern.search(sql):
                return f"upgrade {description} via op.execute()"
    return None


def reachable_upgrade_findings(
    path: Path,
    functions: dict[str, ast.FunctionDef],
    function_name: str,
    seen: set[str],
) -> list[Finding]:
    if function_name in seen:
        return []
    seen.add(function_name)

    function = functions.get(function_name)
    if function is None:
        return []

    findings: list[Finding] = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue

        risk = call_risk(node)
        if risk is not None:
            findings.append(Finding(path=path, line=node.lineno, detail=risk))

        if isinstance(node.func, ast.Name) and node.func.id in functions:
            findings.extend(
                reachable_upgrade_findings(path, functions, node.func.id, seen)
            )

    return findings


def check_migration(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = functions_by_name(tree)
    findings = reachable_upgrade_findings(path, functions, "upgrade", set())
    ack = module_ack(tree)

    failures: list[str] = []
    if findings and not ack:
        failures.append(
            "\n".join(
                [
                    f"{display_path(path)} has destructive upgrade operations without "
                    f'a module-level {ACK_NAME} = "docs/adr/NNNN-...md" acknowledgement:',
                    *(f"  - {finding.display()}" for finding in findings),
                ]
            )
        )

    if ack:
        ack_path = REPO_ROOT / ack
        if not ack_path.is_file():
            failures.append(
                f"{display_path(path)} declares {ACK_NAME}={ack!r}, "
                "but that ADR file does not exist."
            )
        elif findings:
            print(
                f"Accepted {len(findings)} destructive upgrade finding(s) in "
                f"{display_path(path)} via {ack}."
            )

    return failures


def main() -> None:
    failures: list[str] = []
    for path in sorted(MIGRATION_DIR.glob("*.py")):
        failures.extend(check_migration(path))

    if failures:
        print("Alembic migration guardrail check failed:", file=sys.stderr)
        for failure in failures:
            print(f"\n{failure}", file=sys.stderr)
        print(
            "\nUse expand-contract migrations for production changes, or add a short ADR "
            f"and reference it with {ACK_NAME}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print("Alembic migration guardrails passed.")


if __name__ == "__main__":
    main()

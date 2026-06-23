"""Validate Supabase SQL supportability gates.

This is intentionally conservative. A migration that creates public tables must
also enable row level security and define policies for every created table.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"
FORBIDDEN_COLUMN_HINTS = ("api_key", "credential", "secret", "token")


@dataclass(frozen=True)
class MigrationCheck:
    """Validation result for one migration."""

    path: Path
    tables: tuple[str, ...]


def _normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.lower())


def _strip_sql_comments(sql: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in sql.splitlines())


def _find_created_public_tables(sql: str) -> tuple[str, ...]:
    pattern = re.compile(r"create\s+table\s+(?:if\s+not\s+exists\s+)?public\.([a-z_][a-z0-9_]*)")
    return tuple(sorted(set(pattern.findall(sql.lower()))))


def _has_rls(sql: str, table: str) -> bool:
    pattern = rf"alter\s+table\s+public\.{re.escape(table)}\s+enable\s+row\s+level\s+security"
    return re.search(pattern, sql.lower()) is not None


def _has_policy(sql: str, table: str) -> bool:
    pattern = rf"create\s+policy\s+\"?[a-z0-9_ ]+\"?\s+on\s+public\.{re.escape(table)}\s+for\s+"
    return re.search(pattern, sql.lower()) is not None


def _contains_forbidden_column_hint(sql: str) -> bool:
    normalized = _normalize_sql(sql)
    return any(hint in normalized for hint in FORBIDDEN_COLUMN_HINTS)


def validate_migration(path: Path) -> MigrationCheck:
    """Validate one migration file."""
    sql = path.read_text(encoding="utf-8")
    uncommented_sql = _strip_sql_comments(sql)
    if not sql.strip().endswith(";"):
        raise ValueError(f"{path}: migration must end with a semicolon")
    if _contains_forbidden_column_hint(uncommented_sql):
        raise ValueError(f"{path}: migration must not define credential-like storage")

    tables = _find_created_public_tables(sql)
    for table in tables:
        if not _has_rls(sql, table):
            raise ValueError(f"{path}: public.{table} is missing ENABLE ROW LEVEL SECURITY")
        if not _has_policy(sql, table):
            raise ValueError(f"{path}: public.{table} is missing at least one policy")

    return MigrationCheck(path=path, tables=tables)


def main() -> int:
    """Run the SQL supportability gate."""
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        print("SQL gate FAIL: no Supabase migrations found", file=sys.stderr)
        return 1

    try:
        checks = [validate_migration(path) for path in migrations]
    except ValueError as exc:
        print(f"SQL gate FAIL: {exc}", file=sys.stderr)
        return 1

    covered_tables = sorted({table for check in checks for table in check.tables})
    print("SQL gate PASS")
    print(f"migrations_checked={len(checks)}")
    print(f"tables_with_rls_and_policies={','.join(covered_tables)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

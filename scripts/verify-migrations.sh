#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script_dir="$repo_root/scripts"
source "$script_dir/lib/db-url.sh"

migration_url="$(to_pg_url "${MIGRATION_DATABASE_URL:-postgresql://prompteer:prompteer@localhost:5432/prompteer_migration_check}")"
maintenance_url="$(to_pg_url "${MAINTENANCE_DATABASE_URL:-$(maintenance_url_from_url "$migration_url")}")"
migration_database="$(database_name_from_url "$migration_url")"

if ! command -v psql >/dev/null; then
  printf 'Missing required PostgreSQL client binary: psql\n' >&2
  exit 127
fi

drop_database() {
  psql "$maintenance_url" -v ON_ERROR_STOP=1 -v db="$migration_database" <<'SQL'
DROP DATABASE IF EXISTS :"db" WITH (FORCE);
SQL
}

create_database() {
  psql "$maintenance_url" -v ON_ERROR_STOP=1 -v db="$migration_database" <<'SQL'
CREATE DATABASE :"db";
ALTER DATABASE :"db" SET timezone TO 'UTC';
SQL
}

cleanup() {
  if [[ "${KEEP_MIGRATION_CHECK_DATABASE:-false}" == "true" || "$cleanup_enabled" != "true" ]]; then
    return
  fi
  drop_database >/dev/null 2>&1 || true
}

cleanup_enabled=false
trap cleanup EXIT

printf 'Checking PostgreSQL maintenance connection...\n'
psql "$maintenance_url" -v ON_ERROR_STOP=1 -Atc "SELECT 1;" >/dev/null
cleanup_enabled=true

printf 'Preparing throwaway migration database %s...\n' "$migration_database"
drop_database >/dev/null
create_database >/dev/null

printf 'Running Alembic upgrade/downgrade smoke test...\n'
(
  cd "$repo_root/apps/api"
  DATABASE_URL="$(to_sqlalchemy_url "$migration_url")" uv run alembic upgrade head >/dev/null
  DATABASE_URL="$(to_sqlalchemy_url "$migration_url")" uv run alembic current >/dev/null
  DATABASE_URL="$(to_sqlalchemy_url "$migration_url")" uv run alembic downgrade base >/dev/null
  DATABASE_URL="$(to_sqlalchemy_url "$migration_url")" uv run alembic upgrade head >/dev/null
)

users_table="$(
  psql "$migration_url" -v ON_ERROR_STOP=1 -Atc "SELECT to_regclass('public.users');"
)"

llm_usage_table="$(
  psql "$migration_url" -v ON_ERROR_STOP=1 -Atc "SELECT to_regclass('public.llm_usage_days');"
)"

if [[ "$users_table" != "users" || "$llm_usage_table" != "llm_usage_days" ]]; then
  printf 'Expected users and llm_usage_days tables after migration smoke test.\n' >&2
  exit 1
fi

printf 'Alembic migration smoke test succeeded on %s.\n' "$migration_database"

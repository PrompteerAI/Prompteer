#!/usr/bin/env bash
# Exercises backup and restore scripts against disposable PostgreSQL databases.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script_dir="$repo_root/scripts"
source "$script_dir/lib/db-url.sh"
source "$script_dir/lib/load-env.sh"

load_env_file "$repo_root/.env"
apply_local_port_env

base_database_url="$(to_pg_url "${DATABASE_URL:-$DEFAULT_DATABASE_URL}")"
source_url="$(to_pg_url "${SOURCE_DATABASE_URL:-$(database_url_with_name "$base_database_url" prompteer_backup_source)}")"
restore_url="$(to_pg_url "${RESTORE_DATABASE_URL:-$(database_url_with_name "$base_database_url" prompteer_backup_restore)}")"
maintenance_url="$(to_pg_url "${MAINTENANCE_DATABASE_URL:-$(maintenance_url_from_url "$source_url")}")"
dump_path="${1:-${BACKUP_FILE:-$repo_root/.verify/backups/prompteer-roundtrip.dump}}"

for binary in psql pg_dump pg_restore; do
  if ! command -v "$binary" >/dev/null; then
    printf 'Missing required PostgreSQL client binary: %s\n' "$binary" >&2
    exit 127
  fi
done

source_database="$(database_name_from_url "$source_url")"
restore_database="$(database_name_from_url "$restore_url")"

if [[ "$source_url" == "$restore_url" ]]; then
  printf 'SOURCE_DATABASE_URL and RESTORE_DATABASE_URL must point to different databases.\n' >&2
  exit 2
fi

drop_database() {
  local database_name="$1"
  psql "$maintenance_url" -v ON_ERROR_STOP=1 -v db="$database_name" <<'SQL'
DROP DATABASE IF EXISTS :"db" WITH (FORCE);
SQL
}

create_database() {
  local database_name="$1"
  psql "$maintenance_url" -v ON_ERROR_STOP=1 -v db="$database_name" <<'SQL'
CREATE DATABASE :"db";
ALTER DATABASE :"db" SET timezone TO 'UTC';
SQL
}

cleanup() {
  if [[ "${KEEP_BACKUP_RESTORE_DATABASES:-false}" == "true" || "$cleanup_enabled" != "true" ]]; then
    return
  fi

  drop_database "$restore_database" >/dev/null 2>&1 || true
  drop_database "$source_database" >/dev/null 2>&1 || true
}

cleanup_enabled=false
trap cleanup EXIT

printf 'Checking PostgreSQL maintenance connection...\n'
psql "$maintenance_url" -v ON_ERROR_STOP=1 -Atc "SELECT 1;" >/dev/null
cleanup_enabled=true

printf 'Preparing throwaway databases %s and %s...\n' "$source_database" "$restore_database"
drop_database "$restore_database" >/dev/null
drop_database "$source_database" >/dev/null
create_database "$source_database" >/dev/null
create_database "$restore_database" >/dev/null

printf 'Migrating and seeding source database...\n'
(
  cd "$repo_root/apps/api"
  DATABASE_URL="$(to_sqlalchemy_url "$source_url")" uv run python -m app.db.seed >/dev/null
)

printf 'Dumping source database...\n'
BACKUP_DATABASE_URL="$source_url" "$script_dir/backup-db.sh" "$dump_path" >/dev/null

pg_restore --list "$dump_path" | grep -q 'TABLE DATA.*public.*users'
pg_restore --list "$dump_path" | grep -q 'TABLE DATA.*public.*challenges'

printf 'Restoring into clean database...\n'
RESTORE_DATABASE_URL="$restore_url" "$script_dir/restore-db.sh" "$dump_path" >/dev/null

restored_users="$(
  psql "$restore_url" -v ON_ERROR_STOP=1 -Atc \
    "SELECT count(*) FROM users WHERE email IN ('admin@prompteer.dev', 'paid@prompteer.dev', 'free@prompteer.dev');"
)"
restored_challenges="$(
  psql "$restore_url" -v ON_ERROR_STOP=1 -Atc \
    "SELECT count(*) FROM challenges WHERE challenge_number BETWEEN 1 AND 5;"
)"

if [[ "$restored_users" != "3" ]]; then
  printf 'Expected 3 restored demo users, got %s.\n' "$restored_users" >&2
  exit 1
fi

if [[ "$restored_challenges" != "5" ]]; then
  printf 'Expected 5 restored challenges, got %s.\n' "$restored_challenges" >&2
  exit 1
fi

printf 'Backup/restore round trip succeeded: users=%s challenges=%s dump=%s\n' \
  "$restored_users" \
  "$restored_challenges" \
  "$dump_path"

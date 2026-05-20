#!/usr/bin/env bash
set -euo pipefail

input="${1:?usage: scripts/restore-db.sh <dump-file>}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/lib/db-url.sh"

database_url="$(to_pg_url "${RESTORE_DATABASE_URL:-${DATABASE_URL:-$DEFAULT_DATABASE_URL}}")"

pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  --exit-on-error \
  --dbname "$database_url" \
  "$input"

printf 'Restored PostgreSQL backup from %s\n' "$input"

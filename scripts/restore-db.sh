#!/usr/bin/env bash
set -euo pipefail

input="${1:?usage: scripts/restore-db.sh <dump-file>}"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script_dir="$repo_root/scripts"
source "$script_dir/lib/db-url.sh"
source "$script_dir/lib/load-env.sh"

load_env_file "$repo_root/.env"
apply_local_port_env

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

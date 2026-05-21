#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script_dir="$repo_root/scripts"
source "$script_dir/lib/db-url.sh"
source "$script_dir/lib/load-env.sh"

load_env_file "$repo_root/.env"
apply_local_port_env

output="${1:-${BACKUP_FILE:-./backups/prompteer.dump}}"
database_url="$(to_pg_url "${BACKUP_DATABASE_URL:-${DATABASE_URL:-$DEFAULT_DATABASE_URL}}")"

mkdir -p "$(dirname "$output")"
pg_dump --format=custom --file="$output" "$database_url"
pg_restore --list "$output" >/dev/null

printf 'Wrote PostgreSQL custom-format backup to %s\n' "$output"

#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/lib/db-url.sh"

output="${1:-${BACKUP_FILE:-./backups/prompteer.dump}}"
database_url="$(to_pg_url "${BACKUP_DATABASE_URL:-${DATABASE_URL:-$DEFAULT_DATABASE_URL}}")"

mkdir -p "$(dirname "$output")"
pg_dump --format=custom --file="$output" "$database_url"
pg_restore --list "$output" >/dev/null

printf 'Wrote PostgreSQL custom-format backup to %s\n' "$output"

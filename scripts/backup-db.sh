#!/usr/bin/env bash
set -euo pipefail

output="${1:-./backups/prompteer.dump}"
mkdir -p "$(dirname "$output")"
pg_dump -Fc "${DATABASE_URL:-postgresql://prompteer:prompteer@localhost:5432/prompteer}" > "$output"

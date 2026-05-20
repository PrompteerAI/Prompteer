#!/usr/bin/env bash
set -euo pipefail

input="${1:?usage: scripts/restore-db.sh <dump-file>}"
pg_restore --clean --if-exists --dbname "${DATABASE_URL:-postgresql://prompteer:prompteer@localhost:5432/prompteer}" "$input"

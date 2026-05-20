#!/usr/bin/env bash
# PostgreSQL container init hook. Keeps the application database on UTC even when
# POSTGRES_DB is overridden for a local or CI stack.
set -euo pipefail

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=db="$POSTGRES_DB" <<'SQL'
ALTER DATABASE :"db" SET timezone TO 'UTC';
SQL

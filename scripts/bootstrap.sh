#!/usr/bin/env bash
set -euo pipefail

pnpm install
uv sync --project apps/api --dev

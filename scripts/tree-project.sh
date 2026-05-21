#!/usr/bin/env bash
# Print the source-oriented repository tree without dependency, build, cache,
# mock, or verification artifacts.
set -euo pipefail

depth="${1:-3}"

ignore_patterns=(
  '.git'
  '.env'
  '.env.local'
  '.env.*.local'
  'node_modules'
  '.pnpm-store'
  '.venv'
  'venv'
  'env'
  '.next'
  'out'
  'dist'
  'build'
  '.turbo'
  '.ruff_cache'
  '.mypy_cache'
  '.pytest_cache'
  '__pycache__'
  'coverage'
  'coverage.xml'
  'htmlcov'
  'playwright-report'
  'test-results'
  'blob-report'
  '.verify'
  '.mock'
  '.coverage'
  '.coverage.*'
  'next-env.d.ts'
  '*.tsbuildinfo'
  '*.pyc'
  '*.sqlite'
  '*.sqlite3'
  'locales.generated.ts'
)

ignore_glob="$(IFS='|'; printf '%s' "${ignore_patterns[*]}")"

tree -L "$depth" \
  -a \
  -I "$ignore_glob" \
  --dirsfirst

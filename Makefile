.DEFAULT_GOAL := help

.PHONY: help dev lint typecheck test format build verify types types-check backup-restore-check api-dev api-lint api-test seed reset-db

help: ## Show available Makefile targets.
	@awk 'BEGIN {FS = ":.*##"; printf "Available targets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start the local API and web dev servers.
	pnpm dev

lint: ## Run JavaScript and Python lint checks.
	pnpm lint
	cd apps/api && uv run ruff check .

typecheck: ## Run TypeScript and Python type checks.
	pnpm typecheck
	cd apps/api && uv run mypy app

test: ## Run JavaScript and Python tests.
	pnpm test
	cd apps/api && uv run pytest

format: ## Format JavaScript, TypeScript, Markdown, and Python files.
	pnpm format
	cd apps/api && uv run ruff format .

build: ## Build frontend packages.
	pnpm build

verify: ## Run the core local verification suite.
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	$(MAKE) types-check
	$(MAKE) build

types: ## Generate OpenAPI and TypeScript API types.
	cd apps/api && uv run python scripts/export_openapi.py
	pnpm --filter @prompteer/shared-types generate
	pnpm exec prettier --write docs/api/openapi-v1.json packages/shared-types/src/api.ts

types-check: ## Verify generated OpenAPI artifacts are committed.
	scripts/check-openapi-types.sh

backup-restore-check: ## Verify PostgreSQL backup and restore scripts against throwaway databases.
	scripts/verify-backup-restore.sh

api-dev: ## Start the FastAPI development server.
	cd apps/api && uv run fastapi dev app/main.py

api-lint: ## Run Ruff against the API.
	cd apps/api && uv run ruff check .

api-test: ## Run API tests.
	cd apps/api && uv run pytest

seed: ## Seed idempotent local demo data.
	cd apps/api && uv run python -m app.db.seed

reset-db: ## Reset local Docker database and Redis containers.
	scripts/reset-db.sh

.DEFAULT_GOAL := help

.PHONY: help bootstrap dev lint typecheck test audit format build verify env-check types types-check migration-check backup-restore-check compose-deps compose-health e2e verify-ui tree api-dev api-lint api-test seed reset reset-db logs

help: ## Show available Makefile targets.
	@awk 'BEGIN {FS = ":.*##"; printf "Available targets:\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Install deps, start Compose, migrate, and seed local data.
	scripts/bootstrap.sh

dev: ## Start the local API and web dev servers.
	pnpm dev

lint: ## Run JavaScript and Python lint checks.
	pnpm lint
	cd apps/api && uv run ruff check .
	cd apps/api && uv run ruff format --check .

typecheck: ## Run TypeScript and Python type checks.
	pnpm typecheck
	cd apps/api && uv run mypy app tests

test: ## Run JavaScript and Python tests.
	pnpm test
	$(MAKE) compose-deps
	scripts/api-test.sh -q

audit: ## Check JavaScript dependency advisories at moderate severity and above.
	pnpm audit --audit-level moderate

format: ## Format JavaScript, TypeScript, Markdown, and Python files.
	pnpm format
	cd apps/api && uv run ruff format .

build: ## Build frontend packages.
	pnpm build

verify: ## Run the core local verification suite.
	pnpm format:check
	$(MAKE) env-check
	$(MAKE) audit
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
	$(MAKE) types-check
	$(MAKE) build
	$(MAKE) e2e

env-check: ## Verify every referenced environment variable is documented.
	node scripts/check-env-example.mjs

types: ## Generate OpenAPI and TypeScript API types.
	cd apps/api && uv run python scripts/export_openapi.py
	pnpm --filter @prompteer/shared-types generate
	pnpm exec prettier --write docs/api/openapi-v1.json packages/shared-types/src/api.ts

types-check: ## Verify generated OpenAPI artifacts are committed.
	scripts/check-openapi-types.sh

migration-check: ## Verify Alembic upgrade/downgrade against a throwaway PostgreSQL database.
	scripts/verify-migrations.sh

backup-restore-check: ## Verify PostgreSQL backup and restore scripts against throwaway databases.
	scripts/verify-backup-restore.sh

compose-deps: ## Start Docker Compose dependencies required by local tests.
	scripts/compose-up.sh --force-recreate redis

compose-health: ## Assert every Docker Compose service is running and healthy.
	scripts/check-compose-health.sh

e2e: ## Run Playwright end-to-end tests against Docker Compose.
	scripts/compose-up.sh --build
	$(MAKE) compose-health
	bash -lc 'source scripts/lib/load-env.sh; load_env_file ".env"; apply_compose_verification_env; env -u NO_COLOR CI=1 PLAYWRIGHT_BASE_URL="$$PLAYWRIGHT_BASE_URL" pnpm --filter @prompteer/web test:e2e'

verify-ui: ## Capture desktop/mobile screenshots against Docker Compose.
	scripts/compose-up.sh --build
	$(MAKE) compose-health
	bash -lc 'source scripts/lib/load-env.sh; load_env_file ".env"; apply_compose_verification_env; env PROMPTEER_WEB_URL="$$PROMPTEER_WEB_URL" node scripts/verify-ui.mjs'

tree: ## Show the source-oriented repository tree without generated artifacts.
	scripts/tree-project.sh

api-dev: ## Start the FastAPI development server.
	scripts/api-dev.sh

api-lint: ## Run Ruff against the API.
	cd apps/api && uv run ruff check .

api-test: ## Run API tests.
	scripts/api-test.sh

seed: ## Run migrations and seed idempotent local demo data.
	cd apps/api && uv run python -m app.db.seed

reset: ## Reset local Docker database and Redis containers.
	scripts/reset-db.sh

reset-db: ## Reset local Docker database and Redis containers.
	scripts/reset-db.sh

logs: ## Follow local Docker Compose logs.
	docker compose logs -f

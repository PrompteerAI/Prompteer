.PHONY: dev lint typecheck test format api-dev api-lint api-test seed reset-db

dev:
	pnpm dev

lint:
	pnpm lint
	cd apps/api && uv run ruff check .

typecheck:
	pnpm typecheck
	cd apps/api && uv run mypy app

test:
	pnpm test
	cd apps/api && uv run pytest

format:
	pnpm format
	cd apps/api && uv run ruff format .

api-dev:
	cd apps/api && uv run fastapi dev app/main.py

api-lint:
	cd apps/api && uv run ruff check .

api-test:
	cd apps/api && uv run pytest

seed:
	cd apps/api && uv run python -m app.db.seed

reset-db:
	scripts/reset-db.sh

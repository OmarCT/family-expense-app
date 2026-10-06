.PHONY: up down test vectors lint api-gen

up:
	docker compose up -d

down:
	docker compose down

vectors:
	cd services/core && poetry run pytest -m vectors
	pnpm --filter @fea/domain test:vectors

test: vectors
	cd services/core && poetry run pytest
	cd services/workers && poetry run pytest
	pnpm -r test

lint:
	cd services/core && poetry run ruff check . && poetry run mypy .
	cd services/workers && poetry run ruff check . && poetry run mypy .
	pnpm -r lint && pnpm -r typecheck

api-gen:
	pnpm --filter @fea/sync-client generate:api

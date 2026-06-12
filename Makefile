.PHONY: help install dev test lint typecheck format security ci clean docker-up docker-down db-migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	poetry install --no-interaction --only main

dev: ## Install all dependencies (including dev)
	poetry install --no-interaction

# ── Code Quality ──────────────────────────────────────────────────────

lint: ## Run ruff linter
	poetry run ruff check src/ tests/

format: ## Run ruff formatter
	poetry run ruff format src/ tests/

format-check: ## Check formatting without writing
	poetry run ruff format --check src/ tests/

typecheck: ## Run mypy
	poetry run mypy src/ tests/

security: ## Run bandit SAST scan
	poetry run bandit -c pyproject.toml -r src/

check: lint format-check typecheck security ## Run all quality checks

# ── Testing ───────────────────────────────────────────────────────────

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=src --cov-report=term-missing -v

test-integration: ## Run integration tests only
	poetry run pytest -m integration -v

# ── CI Pipeline (local preview) ───────────────────────────────────────

ci: check test-cov ## Run full CI pipeline locally

# ── Docker ────────────────────────────────────────────────────────────

docker-up: ## Start development environment
	docker compose up -d

docker-down: ## Stop development environment
	docker compose down

docker-build: ## Build Docker image
	docker compose build

docker-logs: ## Tail logs from all services
	docker compose logs -f

# ── Database ──────────────────────────────────────────────────────────

db-migrate: ## Run Alembic migrations
	poetry run alembic upgrade head

db-revision: ## Create a new Alembic migration
	poetry run alembic revision --autogenerate -m "$(msg)"

# ── Setup ─────────────────────────────────────────────────────────────

setup: dev ## Full setup (dev deps + pre-commit hooks)
	poetry run pre-commit install --hook-type pre-commit
	poetry run pre-commit install --hook-type pre-push

clean: ## Remove build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov coverage.xml .coverage *.sarif
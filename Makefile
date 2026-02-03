PYTHON ?= python3
VENV ?= .venv
PIP ?= $(VENV)/bin/pip
WEB_PORT ?= 3000
API_PORT ?= 8000

.PHONY: help dev api web test test-api test-web lint lint-web install install-web install-api venv clean

help:
	@echo "Targets:"
	@echo "  make dev         Run API + web in watch mode"
	@echo "  make api         Run FastAPI dev server"
	@echo "  make web         Run Next.js dev server"
	@echo "  make install     Install web + api deps"
	@echo "  make install-web Install web deps (pnpm)"
	@echo "  make install-api Install api deps (venv + pip)"
	@echo "  make test        Run backend tests"
	@echo "  make test-web    Run Playwright tests"
	@echo "  make lint-web    Run Next.js lint"
	@echo "  make clean       Remove caches + venv"

dev:
	@bash -c 'set -e; \
	(cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --port $(API_PORT)) & \
	(cd apps/web && pnpm dev --port $(WEB_PORT)) & \
	wait'

api:
	@cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --port $(API_PORT)

web:
	@cd apps/web && pnpm dev --port $(WEB_PORT)

test:
	@cd apps/api && pytest

test-api:
	@cd apps/api && pytest

test-web:
	@cd apps/web && pnpm test:e2e

lint:
	@cd apps/web && pnpm lint

lint-web:
	@cd apps/web && pnpm lint

install: install-web install-api

install-web:
	@pnpm install

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)

install-api: venv
	@$(PIP) install -r apps/api/requirements.txt

clean:
	@rm -rf $(VENV) apps/api/__pycache__ apps/api/.pytest_cache apps/web/.next apps/web/node_modules

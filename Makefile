.PHONY: help dev build up down logs clean test lint format

# Default target
help:
	@echo "polyhear - Git Multi-Project Dashboard"
	@echo ""
	@echo "Usage:"
	@echo "  make dev        - Start development servers (backend + frontend)"
	@echo "  make build      - Build production Docker image"
	@echo "  make up         - Start production container"
	@echo "  make down       - Stop all containers"
	@echo "  make logs       - Show container logs"
	@echo "  make clean      - Remove containers and volumes"
	@echo ""
	@echo "Development:"
	@echo "  make dev-backend   - Start backend dev server only"
	@echo "  make dev-frontend  - Start frontend dev server only"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo ""
	@echo "Setup:"
	@echo "  make setup         - Initial project setup"
	@echo "  make setup-backend - Setup backend dependencies"
	@echo "  make setup-frontend- Setup frontend dependencies"

# Development
dev:
	docker compose --profile dev up dev-backend dev-frontend

dev-backend:
	docker compose --profile dev up dev-backend

dev-frontend:
	docker compose --profile dev up dev-frontend

# Local development (without Docker)
dev-local-backend:
	cd backend && uv run uvicorn polyhear.main:app --reload --port 8000

dev-local-frontend:
	cd frontend && npm run dev

# Production
build:
	docker compose build polyhear

up:
	docker compose up -d polyhear

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v --rmi local
	rm -rf backend/.venv frontend/node_modules

# Testing
test:
	cd backend && uv run pytest
	cd frontend && npm test

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && npm test

# Linting
lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

lint-backend:
	cd backend && uv run ruff check .

lint-frontend:
	cd frontend && npm run lint

# Formatting
format:
	cd backend && uv run ruff format .
	cd frontend && npm run format

format-backend:
	cd backend && uv run ruff format .

format-frontend:
	cd frontend && npm run format

# Setup
setup: setup-backend setup-frontend
	@echo "Setup complete!"

setup-backend:
	cd backend && uv sync

setup-frontend:
	cd frontend && npm install

# Database
db-migrate:
	cd backend && uv run python -m polyhear.database migrate

db-reset:
	rm -f data/polyhear.db
	$(MAKE) db-migrate

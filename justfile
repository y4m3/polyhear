# polyhear - Git Multi-Project Dashboard
# Just command runner: https://github.com/casey/just

# Load .env.local if exists (for port configuration)
set dotenv-filename := ".env.local"
set dotenv-load := true

# Default values (overridden by .env.local)
polyhear_port := env("POLYHEAR_PORT", "8000")
vite_port := env("VITE_PORT", "5173")

# Worktree name for Docker project isolation
worktree_name := file_name(justfile_directory())

# Export for docker compose
export COMPOSE_PROJECT_NAME := "polyhear-" + worktree_name

# Default recipe - show help
default:
    @just --list

# === Development (Local) ===

# Start backend dev server
dev-local-backend:
    cd backend && POLYHEAR_PORT={{polyhear_port}} uv run uvicorn polyhear.main:app --reload --port {{polyhear_port}}

# Start frontend dev server
dev-local-frontend:
    cd frontend && POLYHEAR_PORT={{polyhear_port}} VITE_PORT={{vite_port}} npm run dev -- --port {{vite_port}}

# === Development (Docker) ===

# Start development servers in Docker
dev:
    docker compose --env-file .env.local --profile dev up dev-backend dev-frontend

# === Production ===

# Build production Docker image
build:
    docker compose --env-file .env.local build polyhear

# Start production container
up:
    docker compose --env-file .env.local up -d polyhear

# Stop all containers
down:
    docker compose --env-file .env.local down

# Show container logs
logs:
    docker compose --env-file .env.local logs -f

# === Setup ===

# Initial project setup
setup: setup-backend setup-frontend

# Setup backend dependencies
setup-backend:
    cd backend && uv sync

# Setup frontend dependencies
setup-frontend:
    cd frontend && npm install

# Setup worktree with automatic port detection
setup-worktree: setup
    #!/usr/bin/env bash
    set -euo pipefail

    mkdir -p data
    chmod +x scripts/find-port.sh

    if [ ! -f .env.local ]; then
        echo "Detecting available ports..."

        BACKEND_PORT=$(scripts/find-port.sh 8000) || {
            echo "ERROR: Failed to find available backend port"
            exit 1
        }

        FRONTEND_PORT=$(scripts/find-port.sh 5173) || {
            echo "ERROR: Failed to find available frontend port"
            exit 1
        }

        {
            echo "POLYHEAR_PORT=$BACKEND_PORT"
            echo "VITE_PORT=$FRONTEND_PORT"
            echo "POLYHEAR_DATA_DIR=data"
        } > .env.local

        echo ""
        echo "Ports auto-assigned:"
        echo "  Backend:  http://localhost:$BACKEND_PORT"
        echo "  Frontend: http://localhost:$FRONTEND_PORT"
    else
        echo ".env.local already exists:"
        cat .env.local
    fi

# === Testing ===

# Run all tests
test: test-backend test-frontend

# Run backend tests
test-backend:
    cd backend && uv run pytest

# Run frontend tests
test-frontend:
    cd frontend && npm test

# === Linting ===

# Run all linters
lint: lint-backend lint-frontend

# Lint backend
lint-backend:
    cd backend && uv run ruff check .

# Lint frontend
lint-frontend:
    cd frontend && npm run lint

# === Formatting ===

# Format all code
format: format-backend format-frontend

# Format backend
format-backend:
    cd backend && uv run ruff format .

# Format frontend
format-frontend:
    cd frontend && npm run format

# === Database ===

# Run database migrations
db-migrate:
    cd backend && uv run python -m polyhear.database migrate

# Reset database
db-reset:
    rm -f data/polyhear.db
    just db-migrate

# === Utilities ===

# Remove containers and clean up
clean:
    docker compose --env-file .env.local down -v --rmi local
    rm -rf backend/.venv frontend/node_modules

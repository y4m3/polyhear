# Multi-stage Dockerfile for polyhear

# ==============================================================================
# Frontend build stage
# ==============================================================================
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Frontend dev stage
# ==============================================================================
FROM node:20-slim AS frontend-dev

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
EXPOSE 5173

# ==============================================================================
# Backend base stage (with uv)
# ==============================================================================
FROM python:3.11-slim AS backend-base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/backend

# ==============================================================================
# Backend dev stage
# ==============================================================================
FROM backend-base AS backend-dev

COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen || uv sync

COPY backend/ ./
COPY config/ /app/config/

ENV PATH="/app/backend/.venv/bin:$PATH"
EXPOSE 8000

# ==============================================================================
# Backend production stage
# ==============================================================================
FROM backend-base AS backend-prod

COPY backend/pyproject.toml backend/uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY backend/ ./
COPY config/ /app/config/

ENV PATH="/app/backend/.venv/bin:$PATH"

# ==============================================================================
# Production image
# ==============================================================================
FROM backend-prod AS production

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Set Python path to include src directory
ENV PYTHONPATH="/app/backend/src:$PYTHONPATH"

# Configure git to trust all directories (for mounted volumes with different ownership)
RUN git config --global --add safe.directory '*'

EXPOSE 8000

CMD ["uvicorn", "polyhear.main:app", "--host", "0.0.0.0", "--port", "8000"]

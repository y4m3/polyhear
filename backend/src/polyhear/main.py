"""FastAPI application entry point for polyhear."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from polyhear.api import projects, settings
from polyhear.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Initialize database on startup
    await init_db()
    yield
    # Cleanup on shutdown (if needed)


app = FastAPI(
    title="polyhear",
    description="Situational awareness for parallel development - Git Multi-Project Dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Serve static files (frontend) in production
frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

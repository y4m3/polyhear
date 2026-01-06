"""Database management for polyhear."""

import os
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from polyhear.config import get_settings
from polyhear.models.db import Base


# Enable foreign keys for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign keys for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_database_path() -> str:
    """Get the database file path."""
    settings = get_settings()

    # Check if custom path is specified in database settings
    if settings.database.path:
        return settings.database.path

    # Default to data directory
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    return str(data_dir / "polyhear.db")


def get_database_url() -> str:
    """Get the database URL for SQLAlchemy."""
    db_path = get_database_path()
    return f"sqlite+aiosqlite:///{db_path}"


# Create async engine
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=os.environ.get("POLYHEAR_DB_ECHO", "").lower() == "true",
        )
    return _engine


def get_session_maker():
    """Get or create the session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session (dependency injection)."""
    async with get_session_maker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize the database (create tables)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None

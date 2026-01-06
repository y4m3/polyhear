"""SQLAlchemy database models for polyhear."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class DBProject(Base):
    """Project model for UI-registered projects."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    build_log: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    test_log: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DBProjectSnapshot(Base):
    """Project state snapshot for history."""

    __tablename__ = "project_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    build_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    test_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    test_passed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_failed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    todo_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fixme_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)


class DBLLMSummary(Base):
    """LLM-generated summary history."""

    __tablename__ = "llm_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    snapshot_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)


class DBBuildLog(Base):
    """Build/test execution history."""

    __tablename__ = "build_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'build' or 'test'
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

"""SQLAlchemy database models for polyhear."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class DBProject(Base):
    """Project model for UI-registered projects."""

    __tablename__ = "projects"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(255), nullable=False, unique=True)
    path: str = Column(String(1024), nullable=False, unique=True)
    group_name: Optional[str] = Column(String(255), nullable=True)
    parent_name: Optional[str] = Column(String(255), nullable=True)
    build_log: Optional[str] = Column(String(1024), nullable=True)
    test_log: Optional[str] = Column(String(1024), nullable=True)
    created_at: datetime = Column(DateTime, default=func.now())
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now())


class DBProjectSnapshot(Base):
    """Project state snapshot for history."""

    __tablename__ = "project_snapshots"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    project_name: str = Column(String(255), nullable=False, index=True)
    branch: Optional[str] = Column(String(255), nullable=True)
    commit_hash: Optional[str] = Column(String(40), nullable=True)
    status_json: Optional[str] = Column(Text, nullable=True)
    build_status: Optional[str] = Column(String(50), nullable=True)
    test_status: Optional[str] = Column(String(50), nullable=True)
    test_passed: Optional[int] = Column(Integer, nullable=True)
    test_failed: Optional[int] = Column(Integer, nullable=True)
    todo_count: Optional[int] = Column(Integer, nullable=True)
    fixme_count: Optional[int] = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, default=func.now(), index=True)


class DBLLMSummary(Base):
    """LLM-generated summary history."""

    __tablename__ = "llm_summaries"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    project_name: str = Column(String(255), nullable=False, index=True)
    snapshot_id: Optional[int] = Column(Integer, nullable=True)
    prompt: Optional[str] = Column(Text, nullable=True)
    response: Optional[str] = Column(Text, nullable=True)
    model: Optional[str] = Column(String(100), nullable=True)
    tokens_used: Optional[int] = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, default=func.now(), index=True)


class DBBuildLog(Base):
    """Build/test execution history."""

    __tablename__ = "build_logs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    project_name: str = Column(String(255), nullable=False, index=True)
    type: str = Column(String(50), nullable=False)  # 'build' or 'test'
    command: Optional[str] = Column(Text, nullable=True)
    exit_code: Optional[int] = Column(Integer, nullable=True)
    stdout: Optional[str] = Column(Text, nullable=True)
    stderr: Optional[str] = Column(Text, nullable=True)
    duration_ms: Optional[int] = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, default=func.now(), index=True)

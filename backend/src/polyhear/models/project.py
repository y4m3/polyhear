"""Pydantic models for project data."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class StatusLevel(str, Enum):
    """Status level enum."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


class WorkingStatus(BaseModel):
    """Git working directory status."""

    clean: bool = True
    staged: int = 0
    modified: int = 0
    untracked: int = 0


class RemoteStatus(BaseModel):
    """Remote tracking status."""

    ahead: int = 0
    behind: int = 0
    tracking: Optional[str] = None


class BuildStatus(BaseModel):
    """Build status from log file."""

    status: StatusLevel = StatusLevel.UNKNOWN
    exit_code: Optional[int] = None
    duration_seconds: Optional[float] = None
    timestamp: Optional[datetime] = None
    message: Optional[str] = None


class TestStatus(BaseModel):
    """Test status from log file."""

    status: StatusLevel = StatusLevel.UNKNOWN
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: Optional[int] = None
    timestamp: Optional[datetime] = None
    failures: list[dict[str, str]] = Field(default_factory=list)


class LastCommit(BaseModel):
    """Last commit information."""

    hash: str
    message: str
    time: str  # Relative time like "5 minutes ago"
    author: Optional[str] = None


class ProjectSummary(BaseModel):
    """Progress summary for a project."""

    completed: Optional[str] = None
    working: Optional[str] = None
    failed: Optional[str] = None
    todos: int = 0
    fixmes: int = 0


class ProjectError(BaseModel):
    """Error information for a project."""

    code: str
    message: str
    suggestion: str
    details: Optional[str] = None


class WorktreeInfo(BaseModel):
    """Git worktree information."""

    path: str
    branch: str
    commit_hash: str
    is_bare: bool = False
    is_detached: bool = False


class Project(BaseModel):
    """Project overview for list view."""

    id: str
    name: str
    path: str
    branch: str
    status: WorkingStatus
    remote: RemoteStatus
    build: BuildStatus
    test: TestStatus
    last_commit: Optional[LastCommit] = None
    summary: ProjectSummary
    error: Optional[ProjectError] = None
    parent: Optional[str] = None  # Parent project name for worktrees
    worktrees: list["Project"] = Field(default_factory=list)


class ProjectDetail(Project):
    """Detailed project information."""

    recent_commits: list[LastCommit] = Field(default_factory=list)
    uncommitted_changes: list[dict[str, str]] = Field(default_factory=list)
    worktree_info: Optional[WorktreeInfo] = None


class ProjectCreate(BaseModel):
    """Request model for creating a project."""

    name: str
    path: str
    group: Optional[str] = None
    parent: Optional[str] = None
    build_log: Optional[str] = None
    test_log: Optional[str] = None


class ProjectListResponse(BaseModel):
    """Response model for project list."""

    projects: list[Project]
    updated_at: datetime

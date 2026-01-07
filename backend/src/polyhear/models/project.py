"""Pydantic models for project data."""

from datetime import datetime
from enum import Enum

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
    tracking: str | None = None


class BuildStatus(BaseModel):
    """Build status from log file."""

    status: StatusLevel = StatusLevel.UNKNOWN
    exit_code: int | None = None
    duration_seconds: float | None = None
    timestamp: datetime | None = None
    message: str | None = None


class TestStatus(BaseModel):
    """Test status from log file."""

    status: StatusLevel = StatusLevel.UNKNOWN
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    duration_ms: int | None = None
    timestamp: datetime | None = None
    failures: list[dict[str, str]] = Field(default_factory=list)


class LastCommit(BaseModel):
    """Last commit information."""

    hash: str
    message: str
    time: str  # Relative time like "5 minutes ago"
    author: str | None = None


class ProjectSummary(BaseModel):
    """Progress summary for a project."""

    completed: str | None = None
    working: str | None = None
    failed: str | None = None
    todos: int = 0
    fixmes: int = 0


class ProjectError(BaseModel):
    """Error information for a project."""

    code: str
    message: str
    suggestion: str
    details: str | None = None


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
    last_commit: LastCommit | None = None
    summary: ProjectSummary
    error: ProjectError | None = None
    parent: str | None = None  # Parent project name for worktrees
    worktrees: list["Project"] = Field(default_factory=list)


class ProjectDetail(Project):
    """Detailed project information."""

    recent_commits: list[LastCommit] = Field(default_factory=list)
    uncommitted_changes: list[dict[str, str]] = Field(default_factory=list)
    worktree_info: WorktreeInfo | None = None


class ProjectCreate(BaseModel):
    """Request model for creating a project."""

    name: str
    path: str
    group: str | None = None
    parent: str | None = None
    build_log: str | None = None
    test_log: str | None = None


class ProjectListResponse(BaseModel):
    """Response model for project list."""

    projects: list[Project]
    updated_at: datetime

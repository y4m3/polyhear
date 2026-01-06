"""Projects API endpoints for polyhear."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from polyhear.config import get_settings
from polyhear.database import get_session
from polyhear.models.db import DBProject
from polyhear.models.project import (
    BuildStatus,
    LastCommit,
    Project,
    ProjectCreate,
    ProjectDetail,
    ProjectListResponse,
    ProjectSummary,
    RemoteStatus,
    TestStatus,
    WorkingStatus,
)
from polyhear.services import build, git, summary

router = APIRouter()


def resolve_path(path: str) -> Path:
    """Resolve a path, handling ~ and relative paths."""
    settings = get_settings()

    # Expand user home directory
    if path.startswith("~"):
        path = str(Path(path).expanduser())

    p = Path(path)

    # If absolute path, use as-is
    if p.is_absolute():
        return p

    # Relative path - relative to repos root
    repos_root = Path(settings.repos_root)
    return repos_root / path


async def collect_project_data(
    project_id: str,
    project_path: Path,
    build_log: str | None = None,
    test_log: str | None = None,
    parent: str | None = None,
    include_detail: bool = False,
) -> Project | ProjectDetail:
    """Collect all data for a project."""
    settings = get_settings()

    # Check if valid git repo
    is_valid, error = await git.check_is_git_repo(project_path)
    if not is_valid:
        # Return minimal project with error
        if include_detail:
            return ProjectDetail(
                id=project_id,
                name=project_id,
                path=str(project_path),
                branch="unknown",
                status=WorkingStatus(),
                remote=RemoteStatus(),
                build=BuildStatus(),
                test=TestStatus(),
                summary=ProjectSummary(),
                error=error,
                parent=parent,
            )
        return Project(
            id=project_id,
            name=project_id,
            path=str(project_path),
            branch="unknown",
            status=WorkingStatus(),
            remote=RemoteStatus(),
            build=BuildStatus(),
            test=TestStatus(),
            summary=ProjectSummary(),
            error=error,
            parent=parent,
        )

    # Collect git information in parallel
    branch_task = git.get_current_branch(project_path)
    status_task = git.get_working_status(project_path)
    remote_task = git.get_remote_status(project_path)
    commits_task = git.get_recent_commits(project_path, count=settings.ui.max_commits)
    build_task = build.get_build_status(project_path, build_log)
    test_task = build.get_test_status(project_path, test_log)

    # Also collect todo counts
    todo_task = git.search_patterns(
        project_path,
        settings.summary.todo_patterns,
        file_extensions=["ts", "tsx", "js", "jsx", "py", "rs", "go", "java", "rb"],
    )

    results = await asyncio.gather(
        branch_task,
        status_task,
        remote_task,
        commits_task,
        build_task,
        test_task,
        todo_task,
        return_exceptions=True,
    )

    # Extract results with proper type handling
    branch: str = results[0] if isinstance(results[0], str) else "unknown"
    status: WorkingStatus = (
        results[1] if isinstance(results[1], WorkingStatus) else WorkingStatus()
    )
    remote: RemoteStatus = (
        results[2] if isinstance(results[2], RemoteStatus) else RemoteStatus()
    )
    commits: list[LastCommit] = (
        results[3] if isinstance(results[3], list) else []
    )
    build_status: BuildStatus = (
        results[4] if isinstance(results[4], BuildStatus) else BuildStatus()
    )
    test_status: TestStatus = (
        results[5] if isinstance(results[5], TestStatus) else TestStatus()
    )
    todo_counts: dict[str, int] = (
        results[6] if isinstance(results[6], dict) else {}
    )

    # Count TODOs and FIXMEs
    todo_count = todo_counts.get("TODO", 0)
    fixme_count = todo_counts.get("FIXME", 0)

    # Get uncommitted changes for summary
    uncommitted: list[dict[str, str]] = []
    if not status.clean:
        uncommitted = await git.get_uncommitted_changes(project_path)

    # Generate summary
    project_summary = summary.generate_project_summary(
        commits=commits,
        status=status,
        uncommitted_changes=uncommitted,
        build_status=build_status,
        test_status=test_status,
        todo_count=todo_count,
        fixme_count=fixme_count,
    )

    last_commit = commits[0] if commits else None

    if include_detail:
        return ProjectDetail(
            id=project_id,
            name=project_id,
            path=str(project_path),
            branch=branch,
            status=status,
            remote=remote,
            build=build_status,
            test=test_status,
            last_commit=last_commit,
            summary=project_summary,
            parent=parent,
            recent_commits=commits,
            uncommitted_changes=uncommitted,
        )

    return Project(
        id=project_id,
        name=project_id,
        path=str(project_path),
        branch=branch,
        status=status,
        remote=remote,
        build=build_status,
        test=test_status,
        last_commit=last_commit,
        summary=project_summary,
        parent=parent,
    )


async def get_all_projects_config(
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """Get all project configurations from both local.toml and database."""
    settings = get_settings()

    # Projects from local.toml
    config_projects: dict[str, dict[str, Any]] = {
        p.name: {
            "name": p.name,
            "path": p.path,
            "parent": p.parent,
            "build_log": p.build_log,
            "test_log": p.test_log,
        }
        for p in settings.projects
    }

    # Projects from database
    result = await session.execute(select(DBProject))
    db_projects = result.scalars().all()

    for db_proj in db_projects:
        # Database entries override local.toml
        config_projects[db_proj.name] = {
            "name": db_proj.name,
            "path": db_proj.path,
            "parent": db_proj.parent_name,
            "build_log": db_proj.build_log,
            "test_log": db_proj.test_log,
        }

    return list(config_projects.values())


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    session: AsyncSession = Depends(get_session),
) -> ProjectListResponse:
    """Get list of all registered projects with their status."""
    project_configs = await get_all_projects_config(session)

    # Collect data for all projects in parallel
    tasks = []
    for config in project_configs:
        path = resolve_path(config["path"])
        tasks.append(
            collect_project_data(
                project_id=config["name"],
                project_path=path,
                build_log=config.get("build_log"),
                test_log=config.get("test_log"),
                parent=config.get("parent"),
            )
        )

    projects = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and convert to list
    valid_projects: list[Project] = [
        p for p in projects
        if isinstance(p, Project) and not isinstance(p, Exception)
    ]

    # Organize worktrees under their parent projects
    parent_map: dict[str, Project] = {}
    orphan_projects: list[Project] = []

    for project in valid_projects:
        if project.parent is None:
            parent_map[project.name] = project
            orphan_projects.append(project)
        # Projects with parents will be added as worktrees below

    # Attach worktrees to parents
    for project in valid_projects:
        if project.parent and project.parent in parent_map:
            parent_map[project.parent].worktrees.append(project)
        elif project.parent:
            # Parent not found, treat as standalone
            orphan_projects.append(project)

    return ProjectListResponse(
        projects=orphan_projects,
        updated_at=datetime.now(),
    )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> ProjectDetail:
    """Get detailed information for a specific project."""
    project_configs = await get_all_projects_config(session)

    # Find the project
    config = next((p for p in project_configs if p["name"] == project_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="Project not found")

    path = resolve_path(config["path"])
    project = await collect_project_data(
        project_id=config["name"],
        project_path=path,
        build_log=config.get("build_log"),
        test_log=config.get("test_log"),
        parent=config.get("parent"),
        include_detail=True,
    )

    if not isinstance(project, ProjectDetail):
        # This shouldn't happen, but handle it just in case
        raise HTTPException(status_code=500, detail="Failed to get project details")

    return project


@router.post("", response_model=Project)
async def create_project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    """Register a new project to monitor."""
    # Check if already exists
    result = await session.execute(
        select(DBProject).where(DBProject.name == project.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Project with this name already exists")

    # Verify the path exists and is a git repo
    path = resolve_path(project.path)
    is_valid, error = await git.check_is_git_repo(path)
    if not is_valid:
        msg = error.message if error else "Invalid path"
        details = error.details if error else ""
        raise HTTPException(status_code=400, detail=f"{msg}: {details}")

    # Create database entry
    db_project = DBProject(
        name=project.name,
        path=project.path,
        group_name=project.group,
        parent_name=project.parent,
        build_log=project.build_log,
        test_log=project.test_log,
    )
    session.add(db_project)
    await session.commit()

    # Return the project data
    project_data = await collect_project_data(
        project_id=project.name,
        project_path=path,
        build_log=project.build_log,
        test_log=project.test_log,
        parent=project.parent,
    )

    if not isinstance(project_data, Project):
        raise HTTPException(status_code=500, detail="Failed to create project")

    return project_data


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Remove a project from monitoring."""
    result = await session.execute(
        select(DBProject).where(DBProject.name == project_id)
    )
    db_project = result.scalar_one_or_none()

    if not db_project:
        # Check if it's a config-only project
        settings = get_settings()
        config_project = next(
            (p for p in settings.projects if p.name == project_id),
            None,
        )
        if config_project:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete project defined in local.toml. Edit the config file instead.",
            )
        raise HTTPException(status_code=404, detail="Project not found")

    await session.delete(db_project)
    await session.commit()

    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/refresh", response_model=Project)
async def refresh_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
) -> Project:
    """Manually refresh a project's status."""
    project_configs = await get_all_projects_config(session)

    # Find the project
    config = next((p for p in project_configs if p["name"] == project_id), None)
    if not config:
        raise HTTPException(status_code=404, detail="Project not found")

    path = resolve_path(config["path"])
    project = await collect_project_data(
        project_id=config["name"],
        project_path=path,
        build_log=config.get("build_log"),
        test_log=config.get("test_log"),
        parent=config.get("parent"),
    )

    if not isinstance(project, Project):
        raise HTTPException(status_code=500, detail="Failed to refresh project")

    return project

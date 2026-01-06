"""Rule-based progress summary generation for polyhear.

MVP: Generates summaries using templates and commit message analysis.
Phase 2: Will add LLM-based summary generation.
"""

import re
from typing import Optional

from polyhear.models.project import (
    BuildStatus,
    LastCommit,
    ProjectSummary,
    StatusLevel,
    TestStatus,
    WorkingStatus,
)


# Conventional commit prefixes
COMMIT_PREFIXES = {
    "feat": "Feature",
    "fix": "Bug fix",
    "docs": "Documentation",
    "style": "Style",
    "refactor": "Refactoring",
    "perf": "Performance",
    "test": "Test",
    "chore": "Chores",
    "build": "Build",
    "ci": "CI",
    "revert": "Revert",
}


def parse_commit_message(message: str) -> tuple[Optional[str], str]:
    """Parse a commit message to extract type and description.

    Returns:
        Tuple of (commit_type, description)
    """
    # Match conventional commit format: type(scope): description
    match = re.match(r"^(\w+)(?:\([^)]+\))?:\s*(.+)$", message, re.IGNORECASE)
    if match:
        commit_type = match.group(1).lower()
        description = match.group(2)
        return commit_type, description

    # No conventional commit prefix
    return None, message


def summarize_commit(message: str) -> str:
    """Summarize a single commit message."""
    commit_type, description = parse_commit_message(message)

    if commit_type and commit_type in COMMIT_PREFIXES:
        type_label = COMMIT_PREFIXES[commit_type]
        return f"{type_label}: {description}"

    return description


def generate_completed_summary(commits: list[LastCommit]) -> Optional[str]:
    """Generate summary of completed work from recent commits."""
    if not commits:
        return None

    # Get the most recent commit
    latest = commits[0]
    commit_type, description = parse_commit_message(latest.message)

    if commit_type:
        type_label = COMMIT_PREFIXES.get(commit_type, commit_type)
        return f"{description}（{type_label}）"

    return latest.message


def generate_working_summary(
    status: WorkingStatus,
    uncommitted_changes: list[dict[str, str]],
) -> Optional[str]:
    """Generate summary of current work in progress."""
    if status.clean:
        return None

    total_changes = status.staged + status.modified + status.untracked

    if total_changes == 0:
        return None

    # Count by file extension to guess what's being worked on
    extensions: dict[str, int] = {}
    for change in uncommitted_changes:
        path = change.get("path", "")
        if "." in path:
            ext = path.rsplit(".", 1)[-1].lower()
            extensions[ext] = extensions.get(ext, 0) + 1

    # Identify common patterns
    work_type = None
    if any(ext in extensions for ext in ["ts", "tsx", "js", "jsx"]):
        work_type = "Frontend"
    elif any(ext in extensions for ext in ["py"]):
        work_type = "Python"
    elif any(ext in extensions for ext in ["rs"]):
        work_type = "Rust"
    elif any(ext in extensions for ext in ["go"]):
        work_type = "Go"
    elif any(ext in extensions for ext in ["css", "scss", "less"]):
        work_type = "Style"
    elif any(ext in extensions for ext in ["md", "txt", "rst"]):
        work_type = "Documentation"
    elif any(ext in extensions for ext in ["test", "spec"]):
        work_type = "Test"

    # Build summary
    parts = []
    if work_type:
        parts.append(work_type)

    change_parts = []
    if status.staged > 0:
        change_parts.append(f"{status.staged} staged")
    if status.modified > 0:
        change_parts.append(f"{status.modified} modified")
    if status.untracked > 0:
        change_parts.append(f"{status.untracked} untracked")

    if change_parts:
        parts.append(", ".join(change_parts))

    if parts:
        return f"In progress: {parts[0]} ({total_changes} files changed)"

    return f"In progress: {total_changes} files changed"


def generate_failed_summary(
    build_status: BuildStatus,
    test_status: TestStatus,
) -> Optional[str]:
    """Generate summary of failures."""
    failures = []

    if build_status.status == StatusLevel.FAIL:
        msg = "Build failed"
        if build_status.message:
            msg += f": {build_status.message}"
        failures.append(msg)

    if test_status.status == StatusLevel.FAIL:
        if test_status.failed > 0:
            msg = f"{test_status.failed} tests failed"
            if test_status.failures:
                first_failure = test_status.failures[0]
                msg += f" ({first_failure.get('name', 'unknown')})"
            failures.append(msg)
        else:
            failures.append("Tests failed")

    if failures:
        return ", ".join(failures)

    return None


def generate_project_summary(
    commits: list[LastCommit],
    status: WorkingStatus,
    uncommitted_changes: list[dict[str, str]],
    build_status: BuildStatus,
    test_status: TestStatus,
    todo_count: int = 0,
    fixme_count: int = 0,
) -> ProjectSummary:
    """Generate a complete project summary.

    Template-based summary generation:
    - completed: Latest commit content
    - working: Uncommitted changes summary (N files changed)
    - failed: Failure details
    - todos: N TODOs, M FIXMEs
    """
    completed = generate_completed_summary(commits)
    working = generate_working_summary(status, uncommitted_changes)
    failed = generate_failed_summary(build_status, test_status)

    return ProjectSummary(
        completed=completed,
        working=working,
        failed=failed,
        todos=todo_count,
        fixmes=fixme_count,
    )

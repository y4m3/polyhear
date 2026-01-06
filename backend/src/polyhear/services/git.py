"""Git operations service for polyhear."""

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path

from polyhear.models.project import (
    LastCommit,
    ProjectError,
    RemoteStatus,
    WorkingStatus,
    WorktreeInfo,
)


@dataclass
class GitCommandResult:
    """Result of a git command execution."""

    stdout: str
    stderr: str
    returncode: int


async def run_git_command(
    repo_path: str | Path,
    args: list[str],
    timeout: float = 30.0,
) -> GitCommandResult:
    """Run a git command asynchronously."""
    cmd = ["git", "-C", str(repo_path)] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )

        return GitCommandResult(
            stdout=stdout.decode("utf-8", errors="replace").strip(),
            stderr=stderr.decode("utf-8", errors="replace").strip(),
            returncode=proc.returncode or 0,
        )

    except TimeoutError:
        raise TimeoutError(f"Git command timed out: {' '.join(cmd)}")
    except FileNotFoundError:
        raise RuntimeError("Git is not installed or not in PATH")


async def check_is_git_repo(path: str | Path) -> tuple[bool, ProjectError | None]:
    """Check if a path is a valid git repository."""
    path = Path(path)

    if not path.exists():
        return False, ProjectError(
            code="PATH_NOT_FOUND",
            message="Path not found",
            suggestion="Please verify the path",
            details=str(path),
        )

    if not path.is_dir():
        return False, ProjectError(
            code="NOT_DIRECTORY",
            message="Not a directory",
            suggestion="Please specify a directory path",
            details=str(path),
        )

    try:
        result = await run_git_command(path, ["rev-parse", "--git-dir"])
        if result.returncode != 0:
            return False, ProjectError(
                code="NOT_GIT_REPO",
                message="Not a Git repository",
                suggestion="Run `git init` or verify the path",
                details=result.stderr,
            )
        return True, None
    except RuntimeError as e:
        return False, ProjectError(
            code="GIT_NOT_FOUND",
            message="Git not found",
            suggestion="Please install Git",
            details=str(e),
        )
    except PermissionError:
        return False, ProjectError(
            code="PERMISSION_DENIED",
            message="Permission denied",
            suggestion="Please check file permissions",
        )


async def get_current_branch(repo_path: str | Path) -> str:
    """Get the current branch name."""
    result = await run_git_command(repo_path, ["branch", "--show-current"])
    if result.returncode == 0 and result.stdout:
        return result.stdout

    # Detached HEAD state - get short commit hash
    result = await run_git_command(repo_path, ["rev-parse", "--short", "HEAD"])
    if result.returncode == 0:
        return f"HEAD@{result.stdout}"

    return "unknown"


async def get_working_status(repo_path: str | Path) -> WorkingStatus:
    """Get the working directory status."""
    result = await run_git_command(repo_path, ["status", "--porcelain"])

    if result.returncode != 0:
        return WorkingStatus()

    staged = 0
    modified = 0
    untracked = 0

    for line in result.stdout.splitlines():
        if not line or len(line) < 2:
            continue

        index_status = line[0]
        worktree_status = line[1]

        # Staged changes (index status is not space or ?)
        if index_status not in (" ", "?"):
            staged += 1

        # Modified in worktree
        if worktree_status == "M":
            modified += 1
        elif worktree_status == "?":
            untracked += 1

    clean = staged == 0 and modified == 0 and untracked == 0

    return WorkingStatus(
        clean=clean,
        staged=staged,
        modified=modified,
        untracked=untracked,
    )


async def get_remote_status(repo_path: str | Path) -> RemoteStatus:
    """Get the status relative to the remote tracking branch."""
    # Get tracking branch
    result = await run_git_command(
        repo_path,
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
    )

    if result.returncode != 0:
        # No upstream set
        return RemoteStatus()

    tracking = result.stdout

    # Get ahead/behind counts
    result = await run_git_command(
        repo_path,
        ["rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
    )

    if result.returncode != 0:
        return RemoteStatus(tracking=tracking)

    parts = result.stdout.split()
    if len(parts) >= 2:
        behind = int(parts[0])
        ahead = int(parts[1])
        return RemoteStatus(ahead=ahead, behind=behind, tracking=tracking)

    return RemoteStatus(tracking=tracking)


async def get_recent_commits(
    repo_path: str | Path,
    count: int = 5,
) -> list[LastCommit]:
    """Get recent commits."""
    # Format: hash|subject|author|relative time
    result = await run_git_command(
        repo_path,
        ["log", f"-n{count}", "--format=%h|%s|%an|%cr"],
    )

    if result.returncode != 0 or not result.stdout:
        return []

    commits = []
    for line in result.stdout.splitlines():
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commits.append(
                LastCommit(
                    hash=parts[0],
                    message=parts[1],
                    author=parts[2],
                    time=parts[3],
                )
            )

    return commits


async def get_uncommitted_changes(repo_path: str | Path) -> list[dict[str, str]]:
    """Get list of uncommitted changes with status."""
    result = await run_git_command(repo_path, ["status", "--porcelain"])

    if result.returncode != 0 or not result.stdout:
        return []

    changes = []
    for line in result.stdout.splitlines():
        if not line or len(line) < 3:
            continue

        status = line[:2].strip()
        filepath = line[3:]

        # Map status codes to readable format
        status_map = {
            "M": "M",  # Modified
            "A": "A",  # Added
            "D": "D",  # Deleted
            "R": "R",  # Renamed
            "C": "C",  # Copied
            "?": "?",  # Untracked
            "!": "!",  # Ignored
        }

        display_status = status_map.get(status[-1] if status else "?", status)

        changes.append({"status": display_status, "path": filepath})

    return changes


async def get_worktrees(repo_path: str | Path) -> list[WorktreeInfo]:
    """Get list of worktrees for this repository."""
    result = await run_git_command(repo_path, ["worktree", "list", "--porcelain"])

    if result.returncode != 0 or not result.stdout:
        return []

    worktrees = []
    current_worktree: dict[str, str] = {}

    for line in result.stdout.splitlines():
        if not line:
            if current_worktree.get("worktree"):
                worktrees.append(
                    WorktreeInfo(
                        path=current_worktree.get("worktree", ""),
                        branch=current_worktree.get("branch", "").replace(
                            "refs/heads/", ""
                        ),
                        commit_hash=current_worktree.get("HEAD", ""),
                        is_bare=current_worktree.get("bare") == "bare",
                        is_detached="detached" in current_worktree,
                    )
                )
            current_worktree = {}
            continue

        if line.startswith("worktree "):
            current_worktree["worktree"] = line[9:]
        elif line.startswith("HEAD "):
            current_worktree["HEAD"] = line[5:]
        elif line.startswith("branch "):
            current_worktree["branch"] = line[7:]
        elif line == "bare":
            current_worktree["bare"] = "bare"
        elif line == "detached":
            current_worktree["detached"] = "detached"

    # Handle last worktree if no trailing empty line
    if current_worktree.get("worktree"):
        worktrees.append(
            WorktreeInfo(
                path=current_worktree.get("worktree", ""),
                branch=current_worktree.get("branch", "").replace("refs/heads/", ""),
                commit_hash=current_worktree.get("HEAD", ""),
                is_bare=current_worktree.get("bare") == "bare",
                is_detached="detached" in current_worktree,
            )
        )

    return worktrees


async def search_patterns(
    repo_path: str | Path,
    patterns: list[str],
    file_extensions: list[str] | None = None,
) -> dict[str, int]:
    """Search for patterns (TODO, FIXME, etc.) in the repository."""
    if not patterns:
        return {}

    # Build grep pattern
    pattern = "|".join(re.escape(p) for p in patterns)

    args = [
        "grep",
        "-c",  # Count matches
        "-E",  # Extended regex
        "-I",  # Ignore binary files
        pattern,
    ]

    # Add file extension filters
    if file_extensions:
        for ext in file_extensions:
            args.extend(["--", f"*.{ext}"])

    result = await run_git_command(repo_path, args)

    # git grep returns 1 if no matches found
    if result.returncode not in (0, 1):
        return {p: 0 for p in patterns}

    # Count total matches
    total_count = 0
    for line in result.stdout.splitlines():
        if ":" in line:
            try:
                count = int(line.split(":")[-1])
                total_count += count
            except ValueError:
                pass

    # For simplicity, distribute count evenly (detailed counting would require separate searches)
    # In practice, we'd run separate searches for each pattern
    counts: dict[str, int] = {}
    for p in patterns:
        counts[p] = 0

    # Run individual pattern searches for accurate counts
    for p in patterns:
        args = ["grep", "-c", "-I", p]
        result = await run_git_command(repo_path, args)
        if result.returncode == 0:
            count = 0
            for line in result.stdout.splitlines():
                if ":" in line:
                    try:
                        count += int(line.split(":")[-1])
                    except ValueError:
                        pass
            counts[p] = count

    return counts


def detect_project_type(repo_path: str | Path) -> str | None:
    """Detect the project type based on files present."""
    path = Path(repo_path)

    if (path / "package.json").exists():
        return "node"
    if (path / "Cargo.toml").exists():
        return "rust"
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists():
        return "python"
    if (path / "go.mod").exists():
        return "go"

    return None

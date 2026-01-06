"""Build and test log reading service for polyhear.

MVP: Reads log files only, does not execute builds/tests.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from polyhear.config import get_settings
from polyhear.models.project import BuildStatus, StatusLevel, TestStatus
from polyhear.services.git import detect_project_type


# Log file search paths by project type
LOG_FILE_PATTERNS = {
    "node": {
        "build_log": [".build.log", "build.log"],
        "test_log": [
            ".test-results.json",
            "test-results.json",
            "coverage/lcov.info",
            ".test.log",
        ],
    },
    "rust": {
        "build_log": ["target/.build.log", ".build.log"],
        "test_log": ["target/.test.log", ".test.log"],
    },
    "python": {
        "build_log": [".build.log", "build.log"],
        "test_log": [
            ".pytest_cache/lastfailed",
            "pytest.log",
            ".test.log",
            "test-results.json",
        ],
    },
    "go": {
        "build_log": [".build.log", "build.log"],
        "test_log": [".test.log", "test.log"],
    },
    "default": {
        "build_log": ["build.log", ".build.log"],
        "test_log": ["test.log", ".test.log"],
    },
}


def find_log_file(
    repo_path: str | Path,
    log_type: str,
    custom_path: Optional[str] = None,
    project_type: Optional[str] = None,
) -> Optional[Path]:
    """Find a log file in the repository.

    Priority:
    1. Custom path from config
    2. Project type specific paths
    3. Default paths
    """
    repo_path = Path(repo_path)

    # 1. Check custom path first
    if custom_path:
        path = repo_path / custom_path
        if path.exists():
            return path

    # 2. Check project type specific paths
    patterns = LOG_FILE_PATTERNS.get(project_type or "default", LOG_FILE_PATTERNS["default"])
    log_paths = patterns.get(log_type, [])

    for log_path in log_paths:
        path = repo_path / log_path
        if path.exists():
            return path

    # 3. Check default paths
    if project_type and project_type != "default":
        default_patterns = LOG_FILE_PATTERNS["default"]
        for log_path in default_patterns.get(log_type, []):
            path = repo_path / log_path
            if path.exists():
                return path

    return None


def parse_build_log(log_path: Path) -> BuildStatus:
    """Parse a build log file.

    Expected format (simple text):
    STATUS: success
    EXIT_CODE: 0
    DURATION: 12s
    TIMESTAMP: 2024-01-15T10:30:00Z
    ---
    <build output>
    """
    try:
        content = log_path.read_text()
    except (IOError, OSError):
        return BuildStatus(status=StatusLevel.UNKNOWN)

    status = StatusLevel.UNKNOWN
    exit_code = None
    duration = None
    timestamp = None
    message = None

    # Parse header section
    header_end = content.find("---")
    header = content[:header_end] if header_end > 0 else content

    for line in header.splitlines():
        line = line.strip()
        if line.startswith("STATUS:"):
            status_str = line[7:].strip().lower()
            if status_str in ("success", "pass", "ok"):
                status = StatusLevel.PASS
            elif status_str in ("fail", "failed", "error"):
                status = StatusLevel.FAIL
        elif line.startswith("EXIT_CODE:"):
            try:
                exit_code = int(line[10:].strip())
                # Infer status from exit code if not explicitly set
                if status == StatusLevel.UNKNOWN:
                    status = StatusLevel.PASS if exit_code == 0 else StatusLevel.FAIL
            except ValueError:
                pass
        elif line.startswith("DURATION:"):
            duration_str = line[9:].strip()
            # Parse duration like "12s", "1m30s", etc.
            match = re.match(r"(\d+(?:\.\d+)?)\s*s", duration_str)
            if match:
                duration = float(match.group(1))
            else:
                match = re.match(r"(\d+)\s*m\s*(\d+)\s*s", duration_str)
                if match:
                    duration = int(match.group(1)) * 60 + int(match.group(2))
        elif line.startswith("TIMESTAMP:"):
            try:
                timestamp = datetime.fromisoformat(line[10:].strip().replace("Z", "+00:00"))
            except ValueError:
                pass
        elif line.startswith("MESSAGE:"):
            message = line[8:].strip()

    # Try to get file modification time as fallback timestamp
    if timestamp is None:
        try:
            timestamp = datetime.fromtimestamp(log_path.stat().st_mtime)
        except OSError:
            pass

    return BuildStatus(
        status=status,
        exit_code=exit_code,
        duration_seconds=duration,
        timestamp=timestamp,
        message=message,
    )


def parse_test_log(log_path: Path) -> TestStatus:
    """Parse a test log file.

    Supports JSON format:
    {
        "status": "failed",
        "passed": 8,
        "failed": 2,
        "skipped": 0,
        "duration_ms": 5432,
        "timestamp": "2024-01-15T10:31:00Z",
        "failures": [...]
    }

    And simple text format:
    STATUS: failed
    PASSED: 8
    FAILED: 2
    TIMESTAMP: 2024-01-15T10:31:00Z
    ---
    FAIL test_name: error message
    """
    try:
        content = log_path.read_text()
    except (IOError, OSError):
        return TestStatus(status=StatusLevel.UNKNOWN)

    # Try JSON format first
    if content.strip().startswith("{"):
        return _parse_test_log_json(content, log_path)

    # Fall back to text format
    return _parse_test_log_text(content, log_path)


def _parse_test_log_json(content: str, log_path: Path) -> TestStatus:
    """Parse JSON format test log."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return TestStatus(status=StatusLevel.UNKNOWN)

    status_str = data.get("status", "").lower()
    if status_str in ("pass", "passed", "success", "ok"):
        status = StatusLevel.PASS
    elif status_str in ("fail", "failed", "error"):
        status = StatusLevel.FAIL
    elif status_str in ("skip", "skipped"):
        status = StatusLevel.SKIPPED
    else:
        status = StatusLevel.UNKNOWN

    timestamp = None
    if "timestamp" in data:
        try:
            timestamp = datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            pass

    failures = []
    for failure in data.get("failures", []):
        if isinstance(failure, dict):
            failures.append({
                "name": failure.get("name", "unknown"),
                "message": failure.get("message", ""),
            })

    return TestStatus(
        status=status,
        passed=data.get("passed", 0),
        failed=data.get("failed", 0),
        skipped=data.get("skipped", 0),
        duration_ms=data.get("duration_ms"),
        timestamp=timestamp,
        failures=failures,
    )


def _parse_test_log_text(content: str, log_path: Path) -> TestStatus:
    """Parse text format test log."""
    status = StatusLevel.UNKNOWN
    passed = 0
    failed = 0
    skipped = 0
    timestamp = None
    failures: list[dict[str, str]] = []

    # Parse header section
    header_end = content.find("---")
    header = content[:header_end] if header_end > 0 else ""
    body = content[header_end + 3:] if header_end > 0 else content

    for line in header.splitlines():
        line = line.strip()
        if line.startswith("STATUS:"):
            status_str = line[7:].strip().lower()
            if status_str in ("pass", "passed", "success", "ok"):
                status = StatusLevel.PASS
            elif status_str in ("fail", "failed", "error"):
                status = StatusLevel.FAIL
        elif line.startswith("PASSED:"):
            try:
                passed = int(line[7:].strip())
            except ValueError:
                pass
        elif line.startswith("FAILED:"):
            try:
                failed = int(line[7:].strip())
            except ValueError:
                pass
        elif line.startswith("SKIPPED:"):
            try:
                skipped = int(line[8:].strip())
            except ValueError:
                pass
        elif line.startswith("TIMESTAMP:"):
            try:
                timestamp = datetime.fromisoformat(
                    line[10:].strip().replace("Z", "+00:00")
                )
            except ValueError:
                pass

    # Parse failure lines
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("FAIL "):
            parts = line[5:].split(":", 1)
            failures.append({
                "name": parts[0].strip(),
                "message": parts[1].strip() if len(parts) > 1 else "",
            })

    # Infer status from counts if not set
    if status == StatusLevel.UNKNOWN:
        if failed > 0:
            status = StatusLevel.FAIL
        elif passed > 0:
            status = StatusLevel.PASS

    # Try to get file modification time as fallback timestamp
    if timestamp is None:
        try:
            timestamp = datetime.fromtimestamp(log_path.stat().st_mtime)
        except OSError:
            pass

    return TestStatus(
        status=status,
        passed=passed,
        failed=failed,
        skipped=skipped,
        timestamp=timestamp,
        failures=failures,
    )


async def get_build_status(
    repo_path: str | Path,
    custom_log_path: Optional[str] = None,
) -> BuildStatus:
    """Get build status from log file."""
    repo_path = Path(repo_path)
    project_type = detect_project_type(repo_path)

    log_file = find_log_file(repo_path, "build_log", custom_log_path, project_type)
    if log_file is None:
        return BuildStatus(status=StatusLevel.UNKNOWN)

    return parse_build_log(log_file)


async def get_test_status(
    repo_path: str | Path,
    custom_log_path: Optional[str] = None,
) -> TestStatus:
    """Get test status from log file."""
    repo_path = Path(repo_path)
    project_type = detect_project_type(repo_path)

    log_file = find_log_file(repo_path, "test_log", custom_log_path, project_type)
    if log_file is None:
        return TestStatus(status=StatusLevel.UNKNOWN)

    return parse_test_log(log_file)

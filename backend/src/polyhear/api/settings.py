"""Settings API endpoints for polyhear."""

from fastapi import APIRouter

from polyhear.config import get_settings

router = APIRouter()


@router.get("")
async def get_ui_settings() -> dict[str, dict[str, str | int | bool | list[str]]]:
    """Get current UI settings."""
    settings = get_settings()

    return {
        "ui": {
            "theme": settings.ui.theme,
            "refresh_interval": settings.ui.refresh_interval,
            "max_commits": settings.ui.max_commits,
        },
        "summary": {
            "scan_todo": settings.summary.scan_todo,
            "todo_patterns": settings.summary.todo_patterns,
        },
        "llm": {
            "enabled": settings.llm.enabled,
            "provider": settings.llm.provider,
        },
    }

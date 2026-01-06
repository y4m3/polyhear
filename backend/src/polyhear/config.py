"""Configuration management for polyhear.

Configuration is loaded from multiple sources with the following priority:
1. Environment variables (highest priority)
2. ~/.config/polyhear/local.toml (machine-specific, not in git)
3. ~/.config/polyhear/config.toml (user customization)
4. config/default.toml (default values, distributed with app)
"""

import os
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class UISettings(BaseModel):
    """UI-related settings."""

    theme: str = "dark"
    refresh_interval: int = 30
    max_commits: int = 5


class SummarySettings(BaseModel):
    """Summary generation settings."""

    scan_todo: bool = True
    todo_patterns: list[str] = Field(default_factory=lambda: ["TODO", "FIXME", "HACK"])


class BuildSettings(BaseModel):
    """Build-related settings."""

    timeout: int = 300


class ProjectTypeDefaults(BaseModel):
    """Default settings for a project type."""

    build_cmd: str = ""
    test_cmd: str = ""
    build_log: str = ".build.log"
    test_log: str = ".test.log"


class DefaultsSettings(BaseModel):
    """Default settings by project type."""

    node: ProjectTypeDefaults = Field(default_factory=lambda: ProjectTypeDefaults(
        build_cmd="npm run build",
        test_cmd="npm test",
        build_log=".build.log",
        test_log=".test-results.json",
    ))
    rust: ProjectTypeDefaults = Field(default_factory=lambda: ProjectTypeDefaults(
        build_cmd="cargo build",
        test_cmd="cargo test",
        build_log="target/.build.log",
        test_log="target/.test.log",
    ))
    python: ProjectTypeDefaults = Field(default_factory=lambda: ProjectTypeDefaults(
        build_cmd="",
        test_cmd="pytest",
        build_log=".build.log",
        test_log="pytest.log",
    ))
    go: ProjectTypeDefaults = Field(default_factory=lambda: ProjectTypeDefaults(
        build_cmd="go build",
        test_cmd="go test ./...",
        build_log=".build.log",
        test_log=".test.log",
    ))


class LLMProviderSettings(BaseModel):
    """LLM provider-specific settings."""

    model: str = ""
    api_key_env: str = ""
    endpoint: str = ""


class LLMSettings(BaseModel):
    """LLM integration settings."""

    enabled: bool = False
    provider: str = "anthropic"
    anthropic: LLMProviderSettings = Field(default_factory=lambda: LLMProviderSettings(
        model="claude-sonnet-4-20250514",
        api_key_env="ANTHROPIC_API_KEY",
    ))
    openai: LLMProviderSettings = Field(default_factory=lambda: LLMProviderSettings(
        model="gpt-4o",
        api_key_env="OPENAI_API_KEY",
    ))
    ollama: LLMProviderSettings = Field(default_factory=lambda: LLMProviderSettings(
        endpoint="http://localhost:11434",
        model="llama3",
    ))


class ProjectConfig(BaseModel):
    """Project configuration from local.toml."""

    name: str
    path: str
    group: str | None = None
    parent: str | None = None
    build_log: str | None = None
    test_log: str | None = None


class DatabaseSettings(BaseModel):
    """Database settings."""

    path: str = ""


class Settings(BaseSettings):
    """Application settings."""

    # Environment variables
    repos_root: str = Field(default="/mnt/repos", alias="POLYHEAR_REPOS_ROOT")
    config_dir: str = Field(default="/app/config", alias="POLYHEAR_CONFIG_DIR")
    data_dir: str = Field(default="/app/data", alias="POLYHEAR_DATA_DIR")
    port: int = Field(default=8000, alias="POLYHEAR_PORT")

    # Path translation for Docker environment
    host_root: str | None = Field(default=None, alias="POLYHEAR_HOST_ROOT")
    host_home: str | None = Field(default=None, alias="POLYHEAR_HOST_HOME")
    container_root: str | None = Field(default=None, alias="POLYHEAR_CONTAINER_ROOT")
    container_home: str | None = Field(default=None, alias="POLYHEAR_CONTAINER_HOME")

    # Loaded from TOML
    ui: UISettings = Field(default_factory=UISettings)
    summary: SummarySettings = Field(default_factory=SummarySettings)
    build: BuildSettings = Field(default_factory=BuildSettings)
    defaults: DefaultsSettings = Field(default_factory=DefaultsSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # Projects from local.toml
    projects: list[ProjectConfig] = Field(default_factory=list)

    class Config:
        env_prefix = "POLYHEAR_"
        extra = "ignore"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file if it exists."""
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def find_config_paths() -> tuple[Path, Path, Path]:
    """Find configuration file paths."""
    # Default config (distributed with app)
    # Try multiple locations for default config
    possible_default_paths = [
        Path(__file__).parent.parent.parent.parent / "config" / "default.toml",  # dev layout
        Path("/app/config/default.toml"),  # docker layout
    ]
    default_config = next(
        (p for p in possible_default_paths if p.exists()), possible_default_paths[0]
    )

    # User config directory
    config_dir = Path(os.environ.get("POLYHEAR_CONFIG_DIR", ""))
    if not config_dir or not config_dir.exists():
        config_dir = Path.home() / ".config" / "polyhear"

    user_config = config_dir / "config.toml"
    local_config = config_dir / "local.toml"

    return default_config, user_config, local_config


def load_config() -> dict[str, Any]:
    """Load and merge configuration from all sources."""
    default_path, user_path, local_path = find_config_paths()

    # Load configs in order of priority (lowest to highest)
    config: dict[str, Any] = {}
    config = deep_merge(config, load_toml(default_path))
    config = deep_merge(config, load_toml(user_path))
    config = deep_merge(config, load_toml(local_path))

    return config


@lru_cache
def get_settings() -> Settings:
    """Get application settings (cached)."""
    config = load_config()
    settings = Settings(**config)
    # Apply path translation for Docker environment
    settings = translate_project_paths(settings)
    return settings


def clear_settings_cache() -> None:
    """Clear the settings cache."""
    get_settings.cache_clear()


def translate_project_path(path: str, settings: Settings) -> str:
    """Translate a project path from host format to container format.

    Supports:
    - Absolute paths: /home/dev/repos/... -> /mnt/repos/...
    - Tilde paths: ~/.local/share/... -> /mnt/home/.local/share/...

    Args:
        path: The path to translate (host-side format)
        settings: Application settings with path translation config

    Returns:
        Translated path suitable for container environment
    """

    # Expand tilde to home directory
    if path.startswith("~"):
        if settings.host_home:
            # Replace ~ with host home directory
            path = path.replace("~", settings.host_home, 1)
        else:
            # Fallback: use Python's path expansion
            path = str(Path(path).expanduser())

    # Convert absolute host paths to container paths
    if settings.host_root and settings.container_root and path.startswith(settings.host_root):
        # Replace host root with container root
        relative = path[len(settings.host_root):].lstrip("/")
        path = str(Path(settings.container_root) / relative)

    # Convert home directory paths to container home paths
    elif settings.host_home and settings.container_home and path.startswith(settings.host_home):
        # Replace host home with container home
        relative = path[len(settings.host_home):].lstrip("/")
        path = str(Path(settings.container_home) / relative)

    return path


def translate_project_paths(settings: Settings) -> Settings:
    """Translate all project paths in settings from host to container format.

    Args:
        settings: Settings with potentially host-side paths

    Returns:
        Settings with translated container-side paths
    """
    if not settings.projects:
        return settings

    # Only translate if we have translation configuration
    needs_translation = (
        settings.host_root and settings.container_root
    ) or (
        settings.host_home and settings.container_home
    )

    if not needs_translation:
        return settings

    # Translate each project path
    translated_projects = []
    for project in settings.projects:
        translated_project = project.model_copy()
        translated_project.path = translate_project_path(project.path, settings)
        translated_projects.append(translated_project)

    settings.projects = translated_projects
    return settings

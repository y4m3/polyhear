"""Tests for docker-compose.yml configuration."""

import subprocess
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    # Navigate from backend/tests to project root
    return Path(__file__).parent.parent.parent


@pytest.fixture
def docker_compose_path(project_root: Path) -> Path:
    """Get the docker-compose.yml path."""
    return project_root / "docker-compose.yml"


@pytest.fixture
def docker_compose_content(docker_compose_path: Path) -> dict:
    """Load and parse docker-compose.yml."""
    with open(docker_compose_path) as f:
        return yaml.safe_load(f)


class TestDockerComposeStructure:
    """Test docker-compose.yml structure for worktree isolation."""

    def test_docker_compose_exists(self, docker_compose_path: Path):
        """Verify docker-compose.yml exists."""
        assert docker_compose_path.exists(), "docker-compose.yml not found"

    def test_has_name_directive(self, docker_compose_path: Path):
        """Verify name directive is present for project isolation."""
        content = docker_compose_path.read_text()
        assert "name:" in content, "name directive not found in docker-compose.yml"

    def test_name_uses_compose_project_name(self, docker_compose_path: Path):
        """Verify name uses COMPOSE_PROJECT_NAME variable."""
        content = docker_compose_path.read_text()
        assert "COMPOSE_PROJECT_NAME" in content, (
            "COMPOSE_PROJECT_NAME variable not used in docker-compose.yml"
        )

    def test_has_dev_backend_service(self, docker_compose_content: dict):
        """Verify dev-backend service exists."""
        assert "services" in docker_compose_content
        assert "dev-backend" in docker_compose_content["services"]

    def test_has_dev_frontend_service(self, docker_compose_content: dict):
        """Verify dev-frontend service exists."""
        assert "services" in docker_compose_content
        assert "dev-frontend" in docker_compose_content["services"]


class TestDevBackendConfig:
    """Test dev-backend service configuration."""

    def test_dev_backend_port_parameterized(self, docker_compose_path: Path):
        """Verify dev-backend port uses POLYHEAR_PORT variable."""
        content = docker_compose_path.read_text()
        # Find dev-backend section and check for POLYHEAR_PORT
        lines = content.split("\n")
        in_dev_backend = False
        found_port_var = False

        for line in lines:
            if "dev-backend:" in line:
                in_dev_backend = True
            elif in_dev_backend and line.strip() and not line.startswith(" "):
                # Exited dev-backend section
                break
            elif in_dev_backend and "POLYHEAR_PORT" in line:
                found_port_var = True
                break

        assert found_port_var, "dev-backend port should use POLYHEAR_PORT environment variable"


class TestDevFrontendConfig:
    """Test dev-frontend service configuration."""

    def test_dev_frontend_port_parameterized(self, docker_compose_path: Path):
        """Verify dev-frontend port uses VITE_PORT variable."""
        content = docker_compose_path.read_text()
        lines = content.split("\n")
        in_dev_frontend = False
        found_port_var = False

        for line in lines:
            if "dev-frontend:" in line:
                in_dev_frontend = True
            elif in_dev_frontend and line.strip() and not line.startswith(" "):
                break
            elif in_dev_frontend and "VITE_PORT" in line:
                found_port_var = True
                break

        assert found_port_var, "dev-frontend port should use VITE_PORT environment variable"

    def test_dev_frontend_has_vite_api_url(self, docker_compose_path: Path):
        """Verify dev-frontend has VITE_API_URL environment variable."""
        content = docker_compose_path.read_text()
        lines = content.split("\n")
        in_dev_frontend = False
        found_vite_api_url = False

        for line in lines:
            if "dev-frontend:" in line:
                in_dev_frontend = True
            elif in_dev_frontend and line.strip() and not line.startswith(" "):
                break
            elif in_dev_frontend and "VITE_API_URL" in line:
                found_vite_api_url = True
                break

        assert found_vite_api_url, "dev-frontend should have VITE_API_URL environment variable"


class TestDockerComposeValidity:
    """Test docker-compose.yml is valid."""

    def test_docker_compose_config_valid(self, project_root: Path):
        """Verify docker-compose config command succeeds."""
        import os
        import tempfile

        # Use a temp directory for POLYHEAR_DATA_DIR to avoid "undefined volume" error
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {
                **dict(os.environ),
                "POLYHEAR_DATA_DIR": tmpdir,
            }
            result = subprocess.run(
                ["docker", "compose", "config", "--quiet"],
                cwd=project_root,
                capture_output=True,
                text=True,
                env=env,
            )
        assert result.returncode == 0, f"docker compose config failed: {result.stderr}"

    def test_environment_variable_substitution(self, project_root: Path):
        """Verify environment variables are properly substituted."""
        import os
        import re
        import tempfile

        # Use a temp directory for POLYHEAR_DATA_DIR to avoid "undefined volume" error
        with tempfile.TemporaryDirectory() as tmpdir:
            env = {
                **dict(os.environ),
                "COMPOSE_PROJECT_NAME": "test-worktree",
                "POLYHEAR_PORT": "9000",
                "VITE_PORT": "9173",
                "POLYHEAR_DATA_DIR": tmpdir,
            }
            # Use --profile dev to include dev-backend and dev-frontend services
            result = subprocess.run(
                ["docker", "compose", "--profile", "dev", "config"],
                cwd=project_root,
                capture_output=True,
                text=True,
                env=env,
            )
        assert result.returncode == 0, f"docker compose config failed: {result.stderr}"

        config_output = result.stdout

        # Verify substitutions
        assert "name: test-worktree" in config_output, (
            "COMPOSE_PROJECT_NAME not substituted correctly"
        )
        # docker compose config may output "9000:8000" or "published: 9000"
        assert re.search(r'(9000:8000|published: "9000")', config_output), (
            "POLYHEAR_PORT not substituted correctly"
        )
        assert re.search(r'(9173:5173|published: "9173")', config_output), (
            "VITE_PORT not substituted correctly"
        )

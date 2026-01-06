"""Basic API tests for polyhear."""

import pytest
from fastapi.testclient import TestClient

from polyhear.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_settings(client):
    """Test settings endpoint."""
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "ui" in data
    assert "theme" in data["ui"]


def test_list_projects_empty(client):
    """Test listing projects when none are registered."""
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "updated_at" in data

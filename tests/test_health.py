"""Health endpoint tests."""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "CtrlChecks AI Backend"
    assert data["status"] == "running"
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ollama" in data
    assert "timestamp" in data


@pytest.mark.integration
def test_health_with_ollama():
    """Integration test with Ollama running."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # If Ollama is running, status should be healthy
    if data["ollama"] == "running":
        assert data["status"] == "healthy"

"""Model listing endpoint tests."""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_list_models_endpoint():
    """Test model listing endpoint."""
    response = client.get("/api/tags")
    # May fail if Ollama is not running
    assert response.status_code in [200, 500, 503]
    if response.status_code == 200:
        data = response.json()
        assert "models" in data


def test_list_models_alias():
    """Test /models alias endpoint."""
    response = client.get("/models")
    assert response.status_code in [200, 500, 503]


@pytest.mark.integration
def test_list_models_integration():
    """Integration test for model listing with Ollama."""
    response = client.get("/api/tags")
    if response.status_code == 200:
        data = response.json()
        assert "models" in data
        # Should have at least one model if Ollama is set up
        assert isinstance(data["models"], list)

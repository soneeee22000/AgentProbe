"""API tests for health and tools endpoints."""

import pytest
from fastapi.testclient import TestClient

from agentprobe.infrastructure.api.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health endpoint should return status ok."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_has_provider_info(self, client: TestClient) -> None:
        """Health should report provider availability."""
        response = client.get("/api/v1/health")
        data = response.json()
        assert "groq_key_set" in data
        assert "tavily_key_set" in data


class TestToolsEndpoint:
    """Tests for the tools listing endpoint."""

    def test_tools_returns_list(self, client: TestClient) -> None:
        """Tools endpoint should return a list of tools."""
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) > 0

    def test_tools_have_required_fields(self, client: TestClient) -> None:
        """Each tool should have name, description, args_schema."""
        response = client.get("/api/v1/tools")
        data = response.json()
        for tool in data["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "args_schema" in tool

    def test_calculator_in_tools(self, client: TestClient) -> None:
        """Calculator should be in the default tool set."""
        response = client.get("/api/v1/tools")
        data = response.json()
        names = [t["name"] for t in data["tools"]]
        assert "calculator" in names

"""API tests for analytics endpoints."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from agentprobe.infrastructure.api.app import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client with lifespan to ensure tables exist."""
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestFailureAnalyticsEndpoint:
    """Tests for the failure analytics endpoint."""

    def test_failure_analytics_returns_ok(self, client: TestClient) -> None:
        """Failure analytics should return 200."""
        response = client.get("/api/v1/analytics/failures")
        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data
        assert "failed_runs" in data
        assert "failure_rate" in data
        assert "by_type" in data

    def test_failure_analytics_empty_db(self, client: TestClient) -> None:
        """Should handle empty database gracefully."""
        response = client.get("/api/v1/analytics/failures")
        data = response.json()
        assert data["total_runs"] >= 0
        assert data["failure_rate"] >= 0.0


class TestModelAnalyticsEndpoint:
    """Tests for the model analytics endpoint."""

    def test_model_analytics_returns_ok(self, client: TestClient) -> None:
        """Model analytics should return 200."""
        response = client.get("/api/v1/analytics/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data

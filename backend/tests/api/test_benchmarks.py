"""API tests for benchmark endpoints."""

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


class TestBenchmarkCasesEndpoint:
    """Tests for benchmark case endpoints."""

    def test_list_cases_empty(self, client: TestClient) -> None:
        """Cases endpoint should return empty list initially."""
        response = client.get("/api/v1/benchmarks/cases")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_case(self, client: TestClient) -> None:
        """Should create a custom benchmark case."""
        payload = {
            "query": "What is 2+2?",
            "category": "math",
            "difficulty": "easy",
            "expected_answer": "4",
            "expected_tools": ["calculator"],
        }
        response = client.post("/api/v1/benchmarks/cases", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["query"] == "What is 2+2?"
        assert data["category"] == "math"
        assert data["is_builtin"] is False

    def test_create_case_invalid_category(self, client: TestClient) -> None:
        """Should reject invalid category."""
        payload = {
            "query": "test",
            "category": "invalid_cat",
            "difficulty": "easy",
            "expected_answer": "test",
        }
        response = client.post("/api/v1/benchmarks/cases", json=payload)
        assert response.status_code == 400

    def test_get_case_not_found(self, client: TestClient) -> None:
        """Should return 404 for nonexistent case."""
        response = client.get("/api/v1/benchmarks/cases/nonexistent")
        assert response.status_code == 404


class TestBenchmarkSuitesEndpoint:
    """Tests for benchmark suite endpoints."""

    def test_list_suites_empty(self, client: TestClient) -> None:
        """Suites endpoint should return empty list initially."""
        response = client.get("/api/v1/benchmarks/suites")
        assert response.status_code == 200
        data = response.json()
        assert "suites" in data
        assert isinstance(data["suites"], list)

    def test_get_suite_not_found(self, client: TestClient) -> None:
        """Should return 404 for nonexistent suite."""
        response = client.get("/api/v1/benchmarks/suites/nonexistent")
        assert response.status_code == 404

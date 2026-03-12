"""Tests for AnalyticsService with mock database."""

from typing import Any

import pytest

from agentprobe.application.services.analytics import AnalyticsService


class MockResult:
    """Mock SQLAlchemy result object."""

    def __init__(self, rows: list) -> None:
        self._rows = rows

    def fetchall(self) -> list:
        """Return all rows."""
        return self._rows

    def scalar_one(self) -> int:
        """Return a single scalar."""
        return self._rows[0] if self._rows else 0


class MockSession:
    """Mock async database session."""

    def __init__(self, results: dict[str, MockResult] | None = None) -> None:
        self._results = results or {}
        self._call_count = 0

    async def execute(self, stmt: Any) -> MockResult:
        """Return mock result based on call order."""
        keys = list(self._results.keys())
        if self._call_count < len(keys):
            result = self._results[keys[self._call_count]]
            self._call_count += 1
            return result
        return MockResult([])

    async def __aenter__(self) -> "MockSession":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


class MockSessionFactory:
    """Mock session factory."""

    def __init__(self, session: MockSession) -> None:
        self._session = session

    def __call__(self) -> MockSession:
        """Return the mock session."""
        return self._session


@pytest.mark.asyncio
async def test_failure_analytics_empty() -> None:
    """Analytics should handle empty database gracefully."""
    session = MockSession({
        "by_type": MockResult([]),
        "by_model": MockResult([]),
        "total": MockResult([0]),
        "failed": MockResult([0]),
    })
    service = AnalyticsService(session_factory=MockSessionFactory(session))
    result = await service.get_failure_analytics()

    assert result["total_runs"] == 0
    assert result["failed_runs"] == 0
    assert result["failure_rate"] == 0.0


@pytest.mark.asyncio
async def test_failure_analytics_with_data() -> None:
    """Analytics should aggregate failure counts correctly."""
    session = MockSession({
        "by_type": MockResult([
            ("hallucinated_tool", 5),
            ("malformed_action", 3),
        ]),
        "by_model": MockResult([
            ("llama-3.1-8b", "hallucinated_tool", 3),
            ("llama-3.1-8b", "malformed_action", 2),
        ]),
        "total": MockResult([10]),
        "failed": MockResult([4]),
    })
    service = AnalyticsService(session_factory=MockSessionFactory(session))
    result = await service.get_failure_analytics()

    assert result["total_runs"] == 10
    assert result["failed_runs"] == 4
    assert result["failure_rate"] == 0.4
    assert result["by_type"]["hallucinated_tool"] == 5


@pytest.mark.asyncio
async def test_model_analytics_empty() -> None:
    """Model analytics should handle empty database."""
    session = MockSession({
        "stats": MockResult([]),
        "steps": MockResult([]),
    })
    service = AnalyticsService(session_factory=MockSessionFactory(session))
    result = await service.get_model_analytics()

    assert result["models"] == {}


@pytest.mark.asyncio
async def test_model_analytics_with_data() -> None:
    """Model analytics should compute per-model stats."""
    session = MockSession({
        "stats": MockResult([
            ("llama-3.1-8b", 20, 15, 1500.0, 150.0),
        ]),
        "steps": MockResult([
            ("llama-3.1-8b", 4.5),
        ]),
    })
    service = AnalyticsService(session_factory=MockSessionFactory(session))
    result = await service.get_model_analytics()

    assert "llama-3.1-8b" in result["models"]
    model = result["models"]["llama-3.1-8b"]
    assert model["total_runs"] == 20
    assert model["success_rate"] == 0.75

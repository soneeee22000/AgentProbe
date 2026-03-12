"""Tests for request validation middleware."""

import pytest
from httpx import ASGITransport, AsyncClient

from agentprobe.infrastructure.api.app import create_app


@pytest.fixture
def app():
    """Create a test app instance."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestRequestValidation:
    """Tests for request validation middleware."""

    async def test_oversized_body_returns_413(self, client: AsyncClient) -> None:
        """Requests exceeding max body size should return 413."""
        # Create a body larger than 1MB
        large_body = "x" * (1_048_577)
        response = await client.post(
            "/api/v1/run",
            content=large_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(large_body)),
            },
        )
        assert response.status_code == 413

    async def test_security_headers_present(self, client: AsyncClient) -> None:
        """Responses should include security headers."""
        response = await client.get("/api/v1/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    async def test_normal_request_passes(self, client: AsyncClient) -> None:
        """Normal-sized requests should pass through."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

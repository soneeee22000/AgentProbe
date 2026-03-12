"""Authentication middleware — JWT and API key validation."""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from agentprobe.application.services.auth import AuthService
from agentprobe.domain.ports.user_repository import IUserRepository

# Paths that don't require authentication
_PUBLIC_PATHS = frozenset({
    "/api/v1/health",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
})

_PUBLIC_PREFIXES = (
    "/auth/",
)


class AuthMiddleware(BaseHTTPMiddleware):
    """Extracts user from Authorization header and attaches to request.state.

    Supports both JWT tokens (``Bearer <token>``) and API keys
    (``Bearer ap_<key>``). Public endpoints are whitelisted.

    Args:
        app: The ASGI application.
        auth_service: Service for JWT verification.
        user_repo: Repository for API key lookups.
    """

    def __init__(
        self,
        app: object,
        auth_service: AuthService,
        user_repo: IUserRepository,
    ) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._auth = auth_service
        self._user_repo = user_repo

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Authenticate the request before processing."""
        path = request.url.path

        # Allow public paths
        if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)

        # Extract Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]  # Strip "Bearer "

        # Try API key first (prefixed with "ap_")
        if token.startswith("ap_"):
            user = await self._user_repo.get_by_api_key(token)
            if not user:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid API key"},
                )
            request.state.user_id = user.id
            return await call_next(request)

        # Try JWT
        user_id = self._auth.verify_token(token)
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        request.state.user_id = user_id
        return await call_next(request)

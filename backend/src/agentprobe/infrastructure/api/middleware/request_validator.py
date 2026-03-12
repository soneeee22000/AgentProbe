"""Request validation middleware for body size limits and security headers."""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class RequestValidatorMiddleware(BaseHTTPMiddleware):
    """Validates request body size and adds security headers.

    Args:
        app: The ASGI application.
        max_body_bytes: Maximum allowed request body size in bytes.
    """

    def __init__(self, app: object, max_body_bytes: int = 1_048_576) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._max_body_bytes = max_body_bytes

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Validate request and add security headers to response."""
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self._max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": (
                        f"Request body too large. "
                        f"Maximum size is {self._max_body_bytes} bytes."
                    ),
                },
            )

        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

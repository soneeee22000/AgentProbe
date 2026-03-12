"""Token-bucket rate limiter middleware."""

import time
from collections import OrderedDict
from dataclasses import dataclass, field

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

_MAX_BUCKETS = 10_000


@dataclass
class TokenBucket:
    """Simple token-bucket rate limiter.

    Tokens refill at a constant rate up to ``capacity``.
    Each request consumes one token. If no tokens remain,
    the request is rejected.
    """

    capacity: float
    refill_rate: float
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        """Initialize bucket at full capacity."""
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume a token.

        Returns:
            True if a token was consumed, False if the bucket is empty.
        """
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limiting middleware using token bucket algorithm.

    Args:
        app: The ASGI application.
        rpm: Maximum requests per minute per client IP.
    """

    def __init__(self, app: object, rpm: int = 60) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._rpm = rpm
        self._buckets: OrderedDict[str, TokenBucket] = OrderedDict()

    def _get_bucket(self, client_ip: str) -> TokenBucket:
        """Get or create a token bucket for the given IP.

        Evicts the oldest entries when the cache exceeds ``_MAX_BUCKETS``
        to prevent unbounded memory growth.
        """
        if client_ip in self._buckets:
            self._buckets.move_to_end(client_ip)
            return self._buckets[client_ip]

        bucket = TokenBucket(
            capacity=float(self._rpm),
            refill_rate=self._rpm / 60.0,
        )
        self._buckets[client_ip] = bucket

        while len(self._buckets) > _MAX_BUCKETS:
            self._buckets.popitem(last=False)

        return bucket

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check rate limit before processing the request."""
        client_ip = request.client.host if request.client else "unknown"
        bucket = self._get_bucket(client_ip)

        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                },
            )

        return await call_next(request)

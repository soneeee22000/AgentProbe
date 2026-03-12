"""Tests for the token-bucket rate limiter."""

import time

from agentprobe.infrastructure.api.middleware.rate_limiter import TokenBucket


class TestTokenBucket:
    """Tests for TokenBucket rate limiter logic."""

    def test_initial_capacity(self) -> None:
        """Bucket starts at full capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=1.0)
        assert bucket.tokens == 10.0

    def test_consume_decrements_tokens(self) -> None:
        """Each consume call decrements by one."""
        bucket = TokenBucket(capacity=5.0, refill_rate=0.0)
        assert bucket.consume()
        assert bucket.tokens < 5.0

    def test_consume_until_empty(self) -> None:
        """Consuming all tokens then returns False."""
        bucket = TokenBucket(capacity=3.0, refill_rate=0.0)
        assert bucket.consume()
        assert bucket.consume()
        assert bucket.consume()
        assert not bucket.consume()

    def test_refill_over_time(self) -> None:
        """Tokens refill based on elapsed time."""
        bucket = TokenBucket(capacity=5.0, refill_rate=100.0)
        # Drain all tokens
        for _ in range(5):
            bucket.consume()
        assert not bucket.consume()

        # Manually advance time by manipulating last_refill
        bucket.last_refill = time.monotonic() - 1.0
        # After 1 second at 100/s refill, should have tokens again
        assert bucket.consume()

    def test_capacity_is_ceiling(self) -> None:
        """Tokens never exceed capacity even with long refill period."""
        bucket = TokenBucket(capacity=5.0, refill_rate=100.0)
        bucket.last_refill = time.monotonic() - 100.0
        bucket.consume()
        # Should be capped at capacity - 1
        assert bucket.tokens <= 5.0

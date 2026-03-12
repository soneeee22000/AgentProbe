"""Pydantic v2 schemas for analytics endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FailureAnalyticsResponse(BaseModel):
    """Aggregated failure analytics."""

    total_runs: int = 0
    failed_runs: int = 0
    failure_rate: float = 0.0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_model: dict[str, dict[str, int]] = Field(default_factory=dict)


class ModelStatsResponse(BaseModel):
    """Per-model performance statistics."""

    total_runs: int = 0
    successes: int = 0
    success_rate: float = 0.0
    avg_duration_ms: float | None = None
    avg_tokens: float | None = None
    avg_steps: float | None = None


class ModelAnalyticsResponse(BaseModel):
    """Aggregated model analytics."""

    models: dict[str, ModelStatsResponse] = Field(default_factory=dict)

"""Analytics API routes — failure and model performance aggregations."""

from fastapi import APIRouter

from agentprobe.application.schemas.analytics import (
    FailureAnalyticsResponse,
    ModelAnalyticsResponse,
)
from agentprobe.infrastructure.api.dependencies import get_analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/failures", response_model=FailureAnalyticsResponse)
async def failure_analytics() -> FailureAnalyticsResponse:
    """Get failure distribution analytics."""
    service = get_analytics_service()
    data = await service.get_failure_analytics()
    return FailureAnalyticsResponse(**data)


@router.get("/models", response_model=ModelAnalyticsResponse)
async def model_analytics() -> ModelAnalyticsResponse:
    """Get per-model performance analytics."""
    service = get_analytics_service()
    data = await service.get_model_analytics()
    return ModelAnalyticsResponse(**data)

"""Health check endpoint."""

from fastapi import APIRouter

from agentprobe.application.schemas.responses import HealthResponse
from agentprobe.infrastructure.api.dependencies import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check with provider availability status."""
    settings = get_settings()
    providers = []

    if settings.groq_api_key:
        providers.append("groq")
    providers.append("ollama")
    if settings.openai_api_key:
        providers.append("openai")
    if settings.anthropic_api_key:
        providers.append("anthropic")
    if settings.google_api_key:
        providers.append("google")

    return HealthResponse(
        status="ok",
        groq_key_set=bool(settings.groq_api_key),
        tavily_key_set=bool(settings.tavily_api_key),
        providers=providers,
    )

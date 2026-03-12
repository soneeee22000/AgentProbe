"""FastAPI application factory for AgentProbe."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentprobe.application.services import BenchmarkSeeder
from agentprobe.infrastructure.api.dependencies import get_settings
from agentprobe.infrastructure.api.routes import (
    agent_router,
    analytics_router,
    benchmarks_router,
    health_router,
    providers_router,
    runs_router,
    tools_router,
)
from agentprobe.infrastructure.persistence.models.database import get_engine
from agentprobe.infrastructure.persistence.models.tables import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — create tables and seed benchmarks on startup."""
    settings = get_settings()
    engine = get_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )

    # Only auto-create tables for SQLite (dev/test). PostgreSQL uses Alembic.
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)
    seeded = await BenchmarkSeeder.seed(
        session_factory, data_path=settings.benchmark_data_path
    )
    logger.info("Benchmark seeder completed — %d cases seeded.", seeded)

    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app with all routes and middleware.
    """
    app = FastAPI(
        title="AgentProbe",
        description="ReAct Agent Observatory — observe, debug, and benchmark LLM agents",
        version="0.3.0",
        lifespan=lifespan,
    )

    # CORS — allow configured origins
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting and request validation
    from agentprobe.infrastructure.api.middleware import (
        RateLimiterMiddleware,
        RequestValidatorMiddleware,
    )

    app.add_middleware(RateLimiterMiddleware, rpm=settings.rate_limit_rpm)
    app.add_middleware(
        RequestValidatorMiddleware,
        max_body_bytes=settings.max_request_body_bytes,
    )

    # Auth middleware (only when auth_enabled)
    if settings.auth_enabled:
        from agentprobe.infrastructure.api.dependencies import (
            get_auth_service,
            get_user_repository,
        )
        from agentprobe.infrastructure.api.middleware.auth import AuthMiddleware

        app.add_middleware(
            AuthMiddleware,
            auth_service=get_auth_service(),
            user_repo=get_user_repository(),
        )

    # Register routes
    from agentprobe.infrastructure.api.routes.auth import router as auth_router
    from agentprobe.infrastructure.api.routes.custom_tools import (
        router as custom_tools_router,
    )
    from agentprobe.infrastructure.api.routes.exports import (
        router as exports_router,
    )
    from agentprobe.infrastructure.api.routes.prompts import (
        router as prompts_router,
    )

    app.include_router(auth_router)
    app.include_router(agent_router)
    app.include_router(runs_router)
    app.include_router(tools_router)
    app.include_router(custom_tools_router)
    app.include_router(prompts_router)
    app.include_router(health_router)
    app.include_router(providers_router)
    app.include_router(benchmarks_router)
    app.include_router(analytics_router)
    app.include_router(exports_router)

    # Legacy v0 routes for backward compatibility during transition
    _register_legacy_routes(app)

    return app


def _register_legacy_routes(app: FastAPI) -> None:
    """Register backward-compatible /api/* routes from v0.

    These forward to v1 handlers so the old frontend keeps working.
    """
    from fastapi.responses import JSONResponse, StreamingResponse

    from agentprobe.application.schemas.requests import RunRequest
    from agentprobe.infrastructure.api.routes.agent import _event_stream

    @app.post("/api/run")
    async def legacy_run(request: RunRequest) -> StreamingResponse:
        """Legacy endpoint — forwards to v1."""
        settings = get_settings()
        if request.provider == "groq" and not settings.groq_api_key:
            return JSONResponse(
                status_code=500,
                content={"detail": "GROQ_API_KEY not set."},
            )
        return StreamingResponse(
            _event_stream(
                query=request.query,
                model=request.model,
                provider=request.provider,
                max_steps=request.max_steps,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/health")
    async def legacy_health() -> dict:
        """Legacy health endpoint."""
        settings = get_settings()
        return {
            "status": "ok",
            "groq_key_set": bool(settings.groq_api_key),
            "tavily_key_set": bool(settings.tavily_api_key),
        }

    @app.get("/api/tools")
    async def legacy_tools() -> dict:
        """Legacy tools endpoint."""
        from agentprobe.infrastructure.api.dependencies import get_tool_registry
        registry = get_tool_registry()
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "args_schema": t.args_schema,
                }
                for t in registry.list_tools()
            ]
        }

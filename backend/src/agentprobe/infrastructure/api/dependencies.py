"""FastAPI dependency injection — wires Clean Architecture together."""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from agentprobe.application.services.analytics import AnalyticsService
from agentprobe.application.services.eval_harness import EvalHarness
from agentprobe.application.services.orchestrator import AgentOrchestrator
from agentprobe.application.services.scoring import ScoringEngine
from agentprobe.domain.ports.benchmark_repository import IBenchmarkRepository
from agentprobe.domain.ports.llm_provider import ILLMProvider
from agentprobe.domain.ports.run_repository import IRunRepository
from agentprobe.domain.ports.tool_registry import IToolRegistry
from agentprobe.infrastructure.config import Settings
from agentprobe.infrastructure.persistence.models.database import (
    get_engine,
    get_session_factory,
)
from agentprobe.infrastructure.persistence.repositories.benchmark_repository import (
    SQLAlchemyBenchmarkRepository,
)
from agentprobe.infrastructure.persistence.repositories.run_repository import (
    SQLAlchemyRunRepository,
)
from agentprobe.infrastructure.providers.anthropic_provider import AnthropicProvider
from agentprobe.infrastructure.providers.google_provider import GoogleProvider
from agentprobe.infrastructure.providers.groq_provider import GroqProvider
from agentprobe.infrastructure.providers.ollama_provider import OllamaProvider
from agentprobe.infrastructure.providers.openai_provider import OpenAIProvider
from agentprobe.infrastructure.tools import create_default_registry


@lru_cache
def get_settings() -> Settings:
    """Load settings singleton from environment/.env file."""
    return Settings()


_providers: dict[str, ILLMProvider] = {}


def get_provider(provider_name: str) -> ILLMProvider:
    """Get or create an LLM provider by name.

    Args:
        provider_name: Provider identifier ('groq', 'ollama', 'openai', 'anthropic', or 'google').

    Returns:
        The LLM provider instance.

    Raises:
        ValueError: If the provider name is not supported.
    """
    if provider_name in _providers:
        return _providers[provider_name]

    settings = get_settings()

    if provider_name == "groq":
        provider = GroqProvider(api_key=settings.groq_api_key)
    elif provider_name == "ollama":
        provider = OllamaProvider(base_url=settings.ollama_base_url)
    elif provider_name == "openai":
        provider = OpenAIProvider(api_key=settings.openai_api_key)
    elif provider_name == "anthropic":
        provider = AnthropicProvider(api_key=settings.anthropic_api_key)
    elif provider_name == "google":
        provider = GoogleProvider(api_key=settings.google_api_key)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    _providers[provider_name] = provider
    return provider


def get_tool_registry() -> IToolRegistry:
    """Create the default tool registry with all built-in tools."""
    settings = get_settings()
    return create_default_registry(
        tavily_api_key=settings.tavily_api_key,
        workspace_path=settings.agent_workspace,
    )


_engine = None
_session_factory = None


def _ensure_db() -> None:
    """Ensure engine and session factory are initialized."""
    global _engine, _session_factory
    settings = get_settings()

    if _engine is None:
        _engine = get_engine(settings.database_url)
    if _session_factory is None:
        _session_factory = get_session_factory(_engine)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    _ensure_db()
    async with _session_factory() as session:
        yield session


def get_run_repository() -> IRunRepository:
    """Create a run repository with the current session factory."""
    _ensure_db()
    return SQLAlchemyRunRepository(session_factory=_session_factory)


def get_benchmark_repository() -> IBenchmarkRepository:
    """Create a benchmark repository with the current session factory."""
    _ensure_db()
    return SQLAlchemyBenchmarkRepository(session_factory=_session_factory)


def get_orchestrator(
    provider_name: str = "groq",
    max_steps: int = 10,
) -> AgentOrchestrator:
    """Create an AgentOrchestrator with all dependencies wired.

    Args:
        provider_name: Which LLM provider to use.
        max_steps: Maximum ReAct loop iterations.

    Returns:
        Fully configured AgentOrchestrator.
    """
    settings = get_settings()
    return AgentOrchestrator(
        llm_provider=get_provider(provider_name),
        tool_registry=get_tool_registry(),
        run_repository=get_run_repository(),
        max_steps=max_steps,
        context_char_limit=settings.context_char_limit,
    )


def get_eval_harness() -> EvalHarness:
    """Create an EvalHarness with benchmark repo and orchestrator factory."""
    return EvalHarness(
        benchmark_repo=get_benchmark_repository(),
        orchestrator_factory=get_orchestrator,
        scoring_engine=ScoringEngine(),
    )


def get_analytics_service() -> AnalyticsService:
    """Create an AnalyticsService with the current session factory."""
    _ensure_db()
    return AnalyticsService(session_factory=_session_factory)


def get_user_repository():  # type: ignore[no-untyped-def]
    """Create a user repository with the current session factory."""
    from agentprobe.infrastructure.persistence.repositories.user_repository import (
        SQLAlchemyUserRepository,
    )
    _ensure_db()
    return SQLAlchemyUserRepository(session_factory=_session_factory)


def get_auth_service():  # type: ignore[no-untyped-def]
    """Create an AuthService with the current settings."""
    from agentprobe.application.services.auth import AuthService
    settings = get_settings()
    return AuthService(
        user_repo=get_user_repository(),
        jwt_secret=settings.jwt_secret,
        jwt_expire_minutes=settings.jwt_expire_minutes,
    )

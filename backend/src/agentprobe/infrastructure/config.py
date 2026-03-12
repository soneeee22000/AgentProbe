"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AgentProbe application.

    Values are loaded from environment variables and an optional ``.env``
    file.  Every field has a sensible default so the app can boot without
    any external configuration during local development.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    groq_api_key: str = ""
    """API key for the Groq inference provider."""

    tavily_api_key: str = ""
    """API key for the Tavily search tool."""

    ollama_base_url: str = "http://localhost:11434"
    """Base URL for a local Ollama instance."""

    openai_api_key: str = ""
    """API key for the OpenAI provider."""

    anthropic_api_key: str = ""
    """API key for the Anthropic provider."""

    google_api_key: str = ""
    """API key for the Google (Gemini) provider."""

    database_url: str = "sqlite+aiosqlite:///./agentprobe.db"
    """Async-compatible database connection string."""

    database_pool_size: int = 5
    """Connection pool size for PostgreSQL."""

    database_max_overflow: int = 10
    """Maximum overflow connections for PostgreSQL."""

    agent_workspace: str = "./workspace"
    """Directory used by agents for temporary file operations."""

    default_model: str = "llama-3.1-8b-instant"
    """Default LLM model identifier."""

    default_provider: str = "groq"
    """Default inference provider name."""

    max_steps: int = 10
    """Maximum number of ReAct loop iterations per run."""

    context_char_limit: int = 24000
    """Maximum character length for the agent context window."""

    benchmark_data_path: str = "./data/benchmark_cases.json"
    """Path to the seed benchmark cases JSON file."""

    rate_limit_rpm: int = 60
    """Maximum requests per minute per client IP."""

    max_request_body_bytes: int = 1_048_576
    """Maximum request body size in bytes (default 1MB)."""

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
    """Allowed CORS origins."""

    environment: str = "development"
    """Application environment (development or production)."""

    jwt_secret: str = "agentprobe-dev-secret-change-in-production"
    """Secret key for JWT token signing."""

    jwt_expire_minutes: int = 1440
    """JWT token expiration time in minutes (default 24h)."""

    auth_enabled: bool = False
    """Feature flag to enable authentication middleware."""

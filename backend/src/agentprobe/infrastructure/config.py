"""Application configuration loaded from environment variables."""

import json

from pydantic import model_validator
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

    default_model: str = "gemini-2.5-flash-lite"
    """Default LLM model identifier — fast + free (Gemini free tier)."""

    default_provider: str = "google"
    """Default inference provider name — picked because Gemini's free tier is the
    most reliable first-impression for the public demo. Override locally via
    ``DEFAULT_PROVIDER``/``DEFAULT_MODEL`` if you want a different default."""

    demo_allowed_providers: str = ""
    """Comma-separated allowlist of providers shown to public users. When set,
    the ``/api/v1/providers`` endpoint filters the catalog to just these names.
    Empty (default) shows everything that has a key configured. Set on the public
    deploy to prevent random visitors from triggering paid OpenAI/Anthropic calls
    against the operator's keys (e.g. ``DEMO_ALLOWED_PROVIDERS=groq,google``)."""

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
    """Allowed CORS origins (defaults). Override with ``CORS_ORIGINS_EXTRA`` to
    append production origins (e.g. the Vercel deploy URL) without losing the
    localhost defaults during development."""

    cors_origins_extra: str = ""
    """Comma-separated additional CORS origins, appended at boot. Set via the
    ``CORS_ORIGINS_EXTRA`` env var, e.g.
    ``CORS_ORIGINS_EXTRA=https://agentprobe.vercel.app,https://www.example.com``.
    JSON list literals are also accepted (``["https://foo","https://bar"]``)."""

    @model_validator(mode="after")
    def _merge_cors_origins(self) -> "Settings":
        raw = self.cors_origins_extra.strip()
        if not raw:
            return self
        if raw.startswith("["):
            try:
                extras = json.loads(raw)
            except json.JSONDecodeError:
                extras = []
        else:
            extras = [item.strip() for item in raw.split(",") if item.strip()]
        if isinstance(extras, list):
            existing = set(self.cors_origins)
            for origin in extras:
                if origin and origin not in existing:
                    self.cors_origins.append(origin)
                    existing.add(origin)
        return self

    environment: str = "development"
    """Application environment (development or production)."""

    jwt_secret: str = "agentprobe-dev-secret-change-in-production"
    """Secret key for JWT token signing."""

    jwt_expire_minutes: int = 1440
    """JWT token expiration time in minutes (default 24h)."""

    auth_enabled: bool = False
    """Feature flag to enable authentication middleware."""

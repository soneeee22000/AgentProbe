"""Provider discovery endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agentprobe.infrastructure.api.dependencies import get_settings

router = APIRouter(prefix="/api/v1", tags=["providers"])


class ProviderModel(BaseModel):
    """Model information within a provider."""

    id: str
    name: str


class ProviderInfo(BaseModel):
    """Provider availability and model information."""

    name: str
    display_name: str
    available: bool
    models: list[ProviderModel] = Field(default_factory=list)


_PROVIDER_CATALOG: list[dict] = [
    {
        "name": "groq",
        "display_name": "Groq",
        "key_field": "groq_api_key",
        "models": [
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant"},
            {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B Versatile"},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
            {"id": "gemma2-9b-it", "name": "Gemma 2 9B IT"},
        ],
    },
    {
        "name": "ollama",
        "display_name": "Ollama (Local)",
        "key_field": None,
        "models": [
            {"id": "llama3.1:8b", "name": "Llama 3.1 8B"},
            {"id": "llama3.1:70b", "name": "Llama 3.1 70B"},
            {"id": "mistral:7b", "name": "Mistral 7B"},
            {"id": "gemma2:9b", "name": "Gemma 2 9B"},
        ],
    },
    {
        "name": "openai",
        "display_name": "OpenAI",
        "key_field": "openai_api_key",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        ],
    },
    {
        "name": "anthropic",
        "display_name": "Anthropic",
        "key_field": "anthropic_api_key",
        "models": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
            {"id": "claude-haiku-4-20250414", "name": "Claude Haiku 4"},
        ],
    },
    {
        "name": "google",
        "display_name": "Google",
        "key_field": "google_api_key",
        "models": [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
            {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite"},
        ],
    },
]


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """Return all providers with their availability and models."""
    settings = get_settings()
    result: list[ProviderInfo] = []

    for catalog_entry in _PROVIDER_CATALOG:
        key_field = catalog_entry["key_field"]
        if key_field is None:
            available = True  # Ollama is always "available" (local)
        else:
            available = bool(getattr(settings, key_field, ""))

        result.append(
            ProviderInfo(
                name=catalog_entry["name"],
                display_name=catalog_entry["display_name"],
                available=available,
                models=[
                    ProviderModel(id=m["id"], name=m["name"])
                    for m in catalog_entry["models"]
                ],
            )
        )

    return result

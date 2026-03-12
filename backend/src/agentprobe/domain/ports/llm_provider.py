"""Port interface for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    completion_tokens: int | None = None
    prompt_tokens: int | None = None
    total_tokens: int | None = None
    model: str = ""


class ILLMProvider(ABC):
    """Abstract interface for LLM providers (Groq, Ollama, etc.).

    Implementations must handle authentication, rate limiting,
    and provider-specific message formatting internally.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request and return a standardized response."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g. 'groq', 'ollama')."""
        ...

    @abstractmethod
    def available_models(self) -> list[str]:
        """Return list of supported model IDs for this provider."""
        ...

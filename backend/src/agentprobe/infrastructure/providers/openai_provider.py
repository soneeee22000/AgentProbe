"""OpenAI LLM provider implementation.

Uses the AsyncOpenAI client for GPT-4o and GPT-4o-mini models.
"""

from openai import AsyncOpenAI

from agentprobe.domain.ports.llm_provider import ILLMProvider, LLMResponse

_DEFAULT_MODELS: list[str] = [
    "gpt-4o",
    "gpt-4o-mini",
]


class OpenAIProvider(ILLMProvider):
    """LLM provider backed by the OpenAI API."""

    def __init__(self, api_key: str) -> None:
        """Initialise the OpenAI provider.

        Args:
            api_key: OpenAI API key used for authentication.
        """
        self._client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to OpenAI.

        Args:
            messages: Conversation history as a list of role/content dicts.
            model: Model identifier (e.g. ``"gpt-4o"``).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            stop: Optional stop sequences. Defaults to ``["Observation:"]``.

        Returns:
            Parsed ``LLMResponse`` with content and token usage.
        """
        if stop is None:
            stop = ["Observation:"]

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            completion_tokens=usage.completion_tokens if usage else None,
            prompt_tokens=usage.prompt_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            model=response.model,
        )

    def provider_name(self) -> str:
        """Return the canonical provider identifier."""
        return "openai"

    def available_models(self) -> list[str]:
        """Return the list of supported OpenAI model identifiers."""
        return list(_DEFAULT_MODELS)

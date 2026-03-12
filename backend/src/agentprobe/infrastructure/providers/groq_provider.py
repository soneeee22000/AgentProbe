"""Groq cloud LLM provider implementation.

Uses the AsyncGroq client to call Groq's hosted inference API
for fast completions on open-weight models.
"""


from groq import AsyncGroq

from agentprobe.domain.ports.llm_provider import ILLMProvider, LLMResponse

_DEFAULT_MODELS: list[str] = [
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


class GroqProvider(ILLMProvider):
    """LLM provider backed by the Groq inference API."""

    def __init__(self, api_key: str) -> None:
        """Initialise the Groq provider.

        Args:
            api_key: Groq API key used for authentication.
        """
        self._client = AsyncGroq(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to Groq.

        The ``stop`` parameter defaults to ``["Observation:"]`` when not
        supplied, which prevents the model from hallucinating tool
        observation blocks in ReAct-style prompting.

        Args:
            messages: Conversation history as a list of role/content dicts.
            model: Model identifier (e.g. ``"llama-3.1-8b-instant"``).
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
            messages=messages,
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
        return "groq"

    def available_models(self) -> list[str]:
        """Return the list of supported Groq model identifiers."""
        return list(_DEFAULT_MODELS)

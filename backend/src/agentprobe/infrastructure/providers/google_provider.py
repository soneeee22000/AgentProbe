"""Google Gemini LLM provider implementation.

Uses the google-genai SDK for Gemini models.
"""

from google import genai
from google.genai import types

from agentprobe.domain.ports.llm_provider import ILLMProvider, LLMResponse

_DEFAULT_MODELS: list[str] = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


class GoogleProvider(ILLMProvider):
    """LLM provider backed by the Google Gemini API."""

    def __init__(self, api_key: str) -> None:
        """Initialise the Google provider.

        Args:
            api_key: Google API key used for authentication.
        """
        self._client = genai.Client(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Send a generate content request to Google Gemini.

        Converts the OpenAI-style messages format into Gemini's
        content format. System messages are passed via system_instruction.

        Args:
            messages: Conversation history as a list of role/content dicts.
            model: Model identifier (e.g. ``"gemini-2.0-flash"``).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            stop: Optional stop sequences. Defaults to ``["Observation:"]``.

        Returns:
            Parsed ``LLMResponse`` with content and token usage.
        """
        if stop is None:
            stop = ["Observation:"]

        # Convert messages to Gemini format
        system_instruction = ""
        contents: list[types.Content] = []

        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=msg["content"])],
                    )
                )

        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            stop_sequences=stop,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        response = await self._client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        content = response.text or ""
        usage_meta = response.usage_metadata

        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        if usage_meta:
            prompt_tokens = usage_meta.prompt_token_count
            completion_tokens = usage_meta.candidates_token_count
            if prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens

        return LLMResponse(
            content=content,
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
            model=model,
        )

    def provider_name(self) -> str:
        """Return the canonical provider identifier."""
        return "google"

    def available_models(self) -> list[str]:
        """Return the list of supported Gemini model identifiers."""
        return list(_DEFAULT_MODELS)

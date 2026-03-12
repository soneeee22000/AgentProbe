"""Anthropic LLM provider implementation.

Uses the AsyncAnthropic client for Claude models.
Anthropic's API uses a separate ``system`` parameter
instead of a system role in the messages list.
"""

from typing import Any

import anthropic

from agentprobe.domain.ports.llm_provider import ILLMProvider, LLMResponse

_DEFAULT_MODELS: list[str] = [
    "claude-sonnet-4-20250514",
    "claude-haiku-4-20250414",
]


class AnthropicProvider(ILLMProvider):
    """LLM provider backed by the Anthropic API."""

    def __init__(self, api_key: str) -> None:
        """Initialise the Anthropic provider.

        Args:
            api_key: Anthropic API key used for authentication.
        """
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Send a message creation request to Anthropic.

        Anthropic requires the system prompt as a separate parameter,
        so we extract it from the messages list if present.

        Args:
            messages: Conversation history as a list of role/content dicts.
            model: Model identifier (e.g. ``"claude-sonnet-4-20250514"``).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            stop: Optional stop sequences. Defaults to ``["Observation:"]``.

        Returns:
            Parsed ``LLMResponse`` with content and token usage.
        """
        if stop is None:
            stop = ["Observation:"]

        # Extract system prompt (Anthropic uses separate param)
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": filtered_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop_sequences": stop,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await self._client.messages.create(**kwargs)

        content = ""
        if response.content:
            text_parts = [
                block.text for block in response.content
                if hasattr(block, "text")
            ]
            content = "".join(text_parts)

        return LLMResponse(
            content=content,
            completion_tokens=response.usage.output_tokens,
            prompt_tokens=response.usage.input_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            model=response.model,
        )

    def provider_name(self) -> str:
        """Return the canonical provider identifier."""
        return "anthropic"

    def available_models(self) -> list[str]:
        """Return the list of supported Anthropic model identifiers."""
        return list(_DEFAULT_MODELS)

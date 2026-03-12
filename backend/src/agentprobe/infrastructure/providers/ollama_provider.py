"""Ollama local LLM provider implementation.

Communicates with a locally-running Ollama server over HTTP
(default ``http://localhost:11434``) for fully offline inference.
"""

from typing import Any

import httpx

from agentprobe.domain.ports.llm_provider import ILLMProvider, LLMResponse

_DEFAULT_BASE_URL = "http://localhost:11434"

_DEFAULT_MODELS: list[str] = [
    "llama3.1:8b",
    "llama3.1:70b",
    "mistral:7b",
    "gemma2:9b",
]


class OllamaProvider(ILLMProvider):
    """LLM provider backed by a local Ollama instance."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 120.0,
    ) -> None:
        """Initialise the Ollama provider.

        Args:
            base_url: Root URL of the Ollama API server.
            timeout: HTTP request timeout in seconds.
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to the local Ollama server.

        The ``stop`` parameter defaults to ``["Observation:"]`` when not
        supplied, which prevents the model from hallucinating tool
        observation blocks in ReAct-style prompting.

        Args:
            messages: Conversation history as a list of role/content dicts.
            model: Model identifier (e.g. ``"llama3.1:8b"``).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            stop: Optional stop sequences. Defaults to ``["Observation:"]``.

        Returns:
            Parsed ``LLMResponse`` with content and token usage.

        Raises:
            httpx.HTTPStatusError: If the Ollama server returns an error.
        """
        if stop is None:
            stop = ["Observation:"]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "stop": stop,
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

        data: dict[str, Any] = response.json()
        content: str = data.get("message", {}).get("content", "")
        eval_count: int | None = data.get("eval_count")
        prompt_eval_count: int | None = data.get("prompt_eval_count")

        total: int | None = None
        if eval_count is not None and prompt_eval_count is not None:
            total = eval_count + prompt_eval_count

        return LLMResponse(
            content=content,
            completion_tokens=eval_count,
            prompt_tokens=prompt_eval_count,
            total_tokens=total,
            model=model,
        )

    def provider_name(self) -> str:
        """Return the canonical provider identifier."""
        return "ollama"

    def available_models(self) -> list[str]:
        """Return the list of supported Ollama model tags."""
        return list(_DEFAULT_MODELS)

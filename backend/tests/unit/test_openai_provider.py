"""Tests for the OpenAI provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentprobe.infrastructure.providers.openai_provider import OpenAIProvider

_DUMMY_KEY = "test-key"


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_provider_name(self) -> None:
        """Provider name should be 'openai'."""
        provider = OpenAIProvider(api_key=_DUMMY_KEY)
        assert provider.provider_name() == "openai"

    def test_available_models(self) -> None:
        """Should return the list of supported models."""
        provider = OpenAIProvider(api_key=_DUMMY_KEY)
        models = provider.available_models()
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models

    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(self) -> None:
        """Complete should return a properly formatted LLMResponse."""
        provider = OpenAIProvider(api_key=_DUMMY_KEY)

        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_usage = MagicMock()
        mock_usage.completion_tokens = 10
        mock_usage.prompt_tokens = 20
        mock_usage.total_tokens = 30
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.model = "gpt-4o"

        with patch.object(
            provider._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="gpt-4o",
            )

        assert result.content == "Test response"
        assert result.total_tokens == 30
        assert result.model == "gpt-4o"

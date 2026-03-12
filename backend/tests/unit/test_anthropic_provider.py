"""Tests for the Anthropic provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentprobe.infrastructure.providers.anthropic_provider import AnthropicProvider

_DUMMY_KEY = "test-key"


class TestAnthropicProvider:
    """Tests for AnthropicProvider."""

    def test_provider_name(self) -> None:
        """Provider name should be 'anthropic'."""
        provider = AnthropicProvider(api_key=_DUMMY_KEY)
        assert provider.provider_name() == "anthropic"

    def test_available_models(self) -> None:
        """Should return the list of supported models."""
        provider = AnthropicProvider(api_key=_DUMMY_KEY)
        models = provider.available_models()
        assert "claude-sonnet-4-20250514" in models
        assert "claude-haiku-4-20250414" in models

    @pytest.mark.asyncio
    async def test_complete_extracts_system_prompt(self) -> None:
        """Complete should separate system messages for Anthropic API."""
        provider = AnthropicProvider(api_key=_DUMMY_KEY)

        mock_content = MagicMock()
        mock_content.text = "Test response"
        mock_usage = MagicMock()
        mock_usage.input_tokens = 20
        mock_usage.output_tokens = 10
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.model = "claude-sonnet-4-20250514"

        with patch.object(
            provider._client.messages,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_create:
            result = await provider.complete(
                messages=[
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"},
                ],
                model="claude-sonnet-4-20250514",
            )

        # Verify system prompt was passed separately
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["system"] == "You are helpful"
        assert all(m["role"] != "system" for m in call_kwargs["messages"])

        assert result.content == "Test response"
        assert result.total_tokens == 30

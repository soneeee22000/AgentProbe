"""Tests for the Google Gemini provider."""

from agentprobe.infrastructure.providers.google_provider import GoogleProvider

_DUMMY_KEY = "test-key"


class TestGoogleProvider:
    """Tests for GoogleProvider."""

    def test_provider_name(self) -> None:
        """Provider name should be 'google'."""
        provider = GoogleProvider(api_key=_DUMMY_KEY)
        assert provider.provider_name() == "google"

    def test_available_models(self) -> None:
        """Should return the list of supported models."""
        provider = GoogleProvider(api_key=_DUMMY_KEY)
        models = provider.available_models()
        assert "gemini-2.0-flash" in models
        assert "gemini-2.0-flash-lite" in models

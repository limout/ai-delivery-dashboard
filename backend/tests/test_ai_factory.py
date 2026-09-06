from unittest.mock import patch

import pytest

from app.ai.factory import get_ai_provider
from app.ai.gemini import GeminiProvider
from app.ai.ollama import OllamaProvider


def test_factory_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)

    with patch("app.ai.factory.OllamaProvider") as provider:
        get_ai_provider()
        provider.assert_called_once()


def test_factory_selects_gemini(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")

    with patch("app.ai.factory.GeminiProvider") as provider:
        get_ai_provider()
        provider.assert_called_once()


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "unknown")

    with pytest.raises(ValueError, match="Unsupported AI_PROVIDER"):
        get_ai_provider()

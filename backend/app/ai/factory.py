from __future__ import annotations

import os

from app.ai.provider import AIProvider
from app.ai.ollama import OllamaProvider
from app.ai.gemini import GeminiProvider


def get_ai_provider() -> AIProvider:
    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()

    if provider == "ollama":
        return OllamaProvider()

    if provider == "gemini":
        return GeminiProvider()

    raise ValueError(
        f"Unsupported AI_PROVIDER: {provider}. "
        "Expected 'ollama' or 'gemini'."
    )

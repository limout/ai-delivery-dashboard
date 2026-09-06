from __future__ import annotations

import os

from google import genai
from google.genai import types

from app.ai.context import AIContext
from app.ai.provider import AIProvider
from app.ai.response import AIStructuredResponse


class GeminiProvider(AIProvider):
    """Gemini-backed provider using Google's Gen AI SDK."""

    SYSTEM_PROMPT = (
        "You are an AI delivery intelligence assistant. "
        "The data source may be Jira, Azure DevOps, or another normalized "
        "delivery source. The source name does not change the required output "
        "format. Use only the supplied delivery context. "
        "Do not invent metrics, events, causes, work item IDs, or facts. "
        "Treat deterministic metrics with data_quality.status 'good' as "
        "authoritative, including valid zero values. "
        "Never return an alternative structure such as summary/detailed_analysis. "
        "Return only JSON matching the supplied schema."
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.model = (
            model
            or os.getenv("GEMINI_MODEL")
            or "gemini-2.5-flash-lite"
        )
        self.client = genai.Client(api_key=self.api_key)

    def analyze(self, context: AIContext, prompt: str) -> str:
        full_prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"Project: {context.project}\n"
            f"Source: {context.source}\n\n"
            f"{prompt}"
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIStructuredResponse,
            ),
        )

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini returned an empty response")

        return str(text).strip()

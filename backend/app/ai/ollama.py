from __future__ import annotations

import os

import requests

from app.ai.context import AIContext
from app.ai.provider import AIProvider
from app.ai.response import AIStructuredResponse


class OllamaProvider(AIProvider):
    def __init__(self, base_url=None, model=None, timeout=120):
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://127.0.0.1:11434"
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3.2"
        self.timeout = timeout

    def analyze(self, context: AIContext, prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "format": AIStructuredResponse.model_json_schema(),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI delivery intelligence assistant. "
                        "The data source may be Jira, Azure DevOps, or another "
                        "normalized delivery source. The source name does not "
                        "change the required output format. "
                        "Use only the supplied delivery context. "
                        "Do not invent metrics, events, causes, or facts. "
                        "Return only valid JSON matching the supplied schema. "
                        "Treat deterministic metrics with data_quality.status "
                        "'good' as authoritative, including valid zero values. "
                        "Never return an alternative structure such as "
                        "summary/detailed_analysis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        return str(
            response.json().get("message", {}).get("content", "")
        ).strip()

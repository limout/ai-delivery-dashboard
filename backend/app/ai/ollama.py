from __future__ import annotations

import os

import requests

from app.ai.context import AIContext
from app.ai.provider import AIProvider
from app.ai.response import AIStructuredResponse


class OllamaProvider(AIProvider):
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://127.0.0.1:11434"
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3.2"
        self.timeout = timeout

    def analyze(self, context: AIContext, prompt: str) -> str:
        schema = AIStructuredResponse.model_json_schema()

        # impact and investigate are part of the new AI contract and must be
        # required in the provider schema. They retain Pydantic defaults so
        # legacy/unit-test responses remain parseable.
        required = list(schema.get("required", []))
        for field in ("impact", "investigate"):
            if field not in required:
                required.append(field)
        schema["required"] = required

        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
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
        return str(response.json().get("message", {}).get("content", "")).strip()

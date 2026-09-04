import os
import requests
from app.ai.context import AIContext
from app.ai.provider import AIProvider

class OllamaProvider(AIProvider):
    def __init__(self, base_url=None, model=None, timeout=120):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL")
                         or "http://127.0.0.1:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "llama3.2"
        self.timeout = timeout

    def analyze(self, context: AIContext, prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI delivery intelligence assistant. "
                        "Use only the supplied delivery context. "
                        "Do not invent metrics, events, causes, or facts. "
                        "If data is missing or insufficient, say so explicitly. "
                        "Separate observed facts from interpretation and recommendations."
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

        print("OLLAMA URL:", f"{self.base_url}/api/chat")
        print("OLLAMA STATUS:", response.status_code)
        print("OLLAMA RESPONSE:", response.text[:2000])

        response.raise_for_status()

        return str(
            response.json().get("message", {}).get("content", "")
        ).strip()

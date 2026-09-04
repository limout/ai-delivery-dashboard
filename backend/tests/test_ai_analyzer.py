import json

import pytest

from app.ai.analyzer import AIAnalyzer
from app.ai.context import AIContext
from app.ai.ollama import OllamaProvider


class FakeProvider:
    model = "fake-model"

    def analyze(self, context, prompt):
        assert context.project == "KAN"
        assert '"value": 9' in prompt
        assert '"value": null' in prompt
        assert "data_quality.status = 'good'" in prompt
        assert "A value of 0 is a valid value" in prompt

        return json.dumps(
            {
                "risk": {
                    "title": "WIP congestion",
                    "severity": "high",
                },
                "facts": [
                    "WIP is 9 items.",
                    "Throughput is 7 items.",
                ],
                "interpretation": [
                    "Work is accumulating faster than it is being completed."
                ],
                "recommendations": [
                    "Review aging work before starting additional work."
                ],
                "data_gaps": [
                    "Cycle time is unavailable because there is insufficient data."
                ],
            }
        )


def test_analyzer_returns_structured_response():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={
            "wip": {"value": 9, "data_quality": {"status": "good"}},
            "cycle_time": {
                "value": None,
                "data_quality": {"status": "insufficient_data"},
            },
        },
        historical={},
        insights=[],
    )

    result = AIAnalyzer(FakeProvider()).analyze(context)

    assert result["project"] == "KAN"
    assert result["model"] == "fake-model"
    assert result["analysis"]["risk"]["title"] == "WIP congestion"
    assert result["analysis"]["risk"]["severity"] == "high"
    assert result["analysis"]["facts"][0] == "WIP is 9 items."
    assert result["analysis"]["interpretation"]
    assert result["analysis"]["recommendations"]
    assert result["analysis"]["data_gaps"]


def test_analyzer_rejects_non_json_response():
    class BadProvider:
        model = "bad-model"

        def analyze(self, context, prompt):
            return "The main risk is WIP accumulation."

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={},
        historical={},
        insights=[],
    )

    with pytest.raises(ValueError, match="non-JSON"):
        AIAnalyzer(BadProvider()).analyze(context)


def test_analyzer_accepts_markdown_json_fallback():
    class MarkdownProvider:
        model = "markdown-model"

        def analyze(self, context, prompt):
            return """```json
{
  "risk": {"title": "WIP congestion", "severity": "high"},
  "facts": ["WIP is 9 items."],
  "interpretation": ["WIP is increasing."],
  "recommendations": ["Review aging work."],
  "data_gaps": []
}
```"""

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={},
        historical={},
        insights=[],
    )

    result = AIAnalyzer(MarkdownProvider()).analyze(context)

    assert result["analysis"]["risk"]["severity"] == "high"


def test_ollama_provider_sends_json_chat_request(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "content": (
                        '{"risk":{"title":"WIP congestion","severity":"high"},'
                        '"facts":[],"interpretation":[],"recommendations":[],'
                        '"data_gaps":[]}'
                    )
                }
            }

    def fake_post(url, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr("app.ai.ollama.requests.post", fake_post)

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={},
        historical={},
        insights=[],
    )

    result = OllamaProvider(
        base_url="http://ollama.test",
        model="test-model",
        timeout=30,
    ).analyze(context, "Analyze this context.")

    assert '"risk"' in result
    assert captured["url"] == "http://ollama.test/api/chat"
    assert captured["json"]["model"] == "test-model"
    assert captured["json"]["stream"] is False
    assert captured["json"]["format"] == "json"
    assert captured["timeout"] == 30

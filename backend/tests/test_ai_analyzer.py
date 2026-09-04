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
                "risk": {"title": "WIP congestion", "severity": "high"},
                "facts": ["WIP is 9"],
                "interpretation": ["The delivery system may be accumulating work."],
                "recommendations": ["Review aging work."],
                "data_gaps": ["Cycle time is unavailable."],
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
    assert result["source"] == "jira"
    assert result["model"] == "fake-model"
    assert result["analysis"]["risk"]["severity"] == "high"
    assert result["analysis"]["facts"] == ["WIP is 9"]


def test_analyzer_rejects_non_json_response():
    class InvalidProvider:
        model = "fake-model"

        def analyze(self, context, prompt):
            return "This is not JSON"

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
    )

    with pytest.raises(ValueError, match="non-JSON"):
        AIAnalyzer(InvalidProvider()).analyze(context)


def test_analyzer_rejects_wrong_json_schema():
    class WrongSchemaProvider:
        model = "fake-model"

        def analyze(self, context, prompt):
            return json.dumps(
                {
                    "summary": {"current_wip": 2},
                    "detailed_analysis": {},
                }
            )

    context = AIContext(
        project="KAN",
        source="azure_devops",
        analysis_window_days=14,
    )

    with pytest.raises(ValueError, match="invalid response schema"):
        AIAnalyzer(WrongSchemaProvider()).analyze(context)


def test_analyzer_accepts_markdown_json_response():
    class MarkdownProvider:
        model = "fake-model"

        def analyze(self, context, prompt):
            return """
```json
{
    "risk": {
        "title": "WIP congestion",
        "severity": "high"
    },
    "facts": ["WIP is 9"],
    "interpretation": ["Potential congestion"],
    "recommendations": ["Review aging work"],
    "data_gaps": []
}
```
"""

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
    )

    result = AIAnalyzer(MarkdownProvider()).analyze(context)
    assert result["analysis"]["risk"]["title"] == "WIP congestion"


def test_ollama_provider_requests_json_format(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {
                    "content": '{"risk":{"title":"test","severity":"low"}}'
                }
            }

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.ai.ollama.requests.post", fake_post)

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="qwen3:8b",
    )

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
    )

    provider.analyze(context=context, prompt="test prompt")

    assert captured["json"]["format"] == "json"


def test_parser_normalizes_single_string_fields():
    raw = """
{
    "risk": {
        "title": "WIP congestion",
        "severity": "high"
    },
    "facts": "WIP is 9",
    "interpretation": "The system may be accumulating work",
    "recommendations": "Review aging work",
    "data_gaps": null
}
"""

    result = AIAnalyzer._parse_response(raw)

    assert result.facts == ["WIP is 9"]
    assert result.interpretation == ["The system may be accumulating work"]
    assert result.recommendations == ["Review aging work"]
    assert result.data_gaps == []


def test_parser_rejects_invalid_severity():
    raw = """
{
    "risk": {
        "title": "WIP congestion",
        "severity": "critical"
    },
    "facts": [],
    "interpretation": [],
    "recommendations": [],
    "data_gaps": []
}
"""

    with pytest.raises(ValueError, match="severity"):
        AIAnalyzer._parse_response(raw)

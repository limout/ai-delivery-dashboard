import json

import pytest

from app.ai.analyzer import AIAnalyzer
from app.ai.context import AIContext
from app.ai.response import AIStructuredResponse
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
                    "WIP is 9",
                ],
                "interpretation": [
                    "The delivery system may be accumulating work.",
                ],
                "recommendations": [
                    "Review aging work.",
                ],
                "data_gaps": [
                    "Cycle time is unavailable.",
                ],
            }
        )


def test_analyzer_returns_structured_response():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={
            "wip": {
                "value": 9,
                "data_quality": {
                    "status": "good",
                },
            },
            "cycle_time": {
                "value": None,
                "data_quality": {
                    "status": "insufficient_data",
                },
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

    monkeypatch.setattr(
        "app.ai.ollama.requests.post",
        fake_post,
    )

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model="qwen3:8b",
    )

    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
    )

    provider.analyze(
        context=context,
        prompt="test prompt",
    )

    schema = captured["json"]["format"]
    expected_schema = AIStructuredResponse.model_json_schema()

    assert schema["type"] == expected_schema["type"]
    assert schema["properties"] == expected_schema["properties"]

    # impact and investigate are part of the provider contract even though
    # the Pydantic model keeps defaults for backward-compatible parsing.
    assert set(schema["required"]) == {
        "risk",
        "facts",
        "interpretation",
        "impact",
        "investigate",
        "recommendations",
        "data_gaps",
    }


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
    assert result.interpretation == [
        "The system may be accumulating work"
    ]
    assert result.recommendations == ["Review aging work"]
    assert result.data_gaps == []


def test_analyzer_retries_unknown_work_item_reference():
    class RetryProvider:
        model = "fake-model"

        def __init__(self):
            self.prompts = []
            self.calls = 0

        def analyze(self, context, prompt):
            self.calls += 1
            self.prompts.append(prompt)
            if self.calls == 1:
                return json.dumps({
                    "risk": {"title": "JRA-123 is at risk", "severity": "high"},
                    "facts": [],
                    "interpretation": [],
                    "recommendations": [],
                    "data_gaps": [],
                })

            return json.dumps({
                "risk": {"title": "Delivery risk", "severity": "high"},
                "facts": ["JRA-101 is in progress"],
                "interpretation": [],
                "recommendations": [],
                "data_gaps": [],
            })

    provider = RetryProvider()
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        insights=[
            {
                "id": "insight-1",
                "evidence": {
                    "work_items": [
                        {"id": "JRA-101", "title": "Real item"},
                    ]
                },
            }
        ],
    )

    result = AIAnalyzer(provider).analyze(context)

    assert provider.calls == 2
    assert "JRA-101" in provider.prompts[0]
    assert "AUTHORITATIVE WORK ITEM IDS: JRA-101" in provider.prompts[1]
    assert result["analysis"]["facts"] == ["JRA-101 is in progress"]


def test_analyzer_retries_unsupported_data_gap():
    class RetryProvider:
        model = "fake-model"

        def __init__(self):
            self.prompts = []
            self.calls = 0

        def analyze(self, context, prompt):
            self.calls += 1
            self.prompts.append(prompt)
            if self.calls == 1:
                return json.dumps({
                    "risk": {"title": "Delivery risk", "severity": "medium"},
                    "facts": ["WIP is 9"],
                    "interpretation": [],
                    "recommendations": [],
                    "data_gaps": ["cycle_time"],
                })

            return json.dumps({
                "risk": {"title": "Delivery risk", "severity": "medium"},
                "facts": ["WIP is 9"],
                "interpretation": [],
                "recommendations": [],
                "data_gaps": [],
            })

    provider = RetryProvider()
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={
            "wip": {
                "value": 9,
                "data_quality": {"status": "good"},
            },
            "cycle_time": {
                "value": 12,
                "data_quality": {"status": "good"},
            },
        },
        historical={
            "cycle_time": {"values": [10, 11, 12]},
        },
        data_gaps=[],
    )

    result = AIAnalyzer(provider).analyze(context)

    # data_gaps are deterministic backend output and are normalized before
    # validation, so an LLM-only data-gap error must not trigger a retry.
    assert provider.calls == 1
    assert result["analysis"]["data_gaps"] == []


def test_ai_analyzer_uses_authoritative_context_data_gaps():
    from app.ai.analyzer import AIAnalyzer
    from app.ai.context import AIContext
    from app.ai.response import AIStructuredResponse

    class FakeProvider:
        model = "test-model"

        def analyze(self, context, prompt):
            return AIStructuredResponse(
                risk={"title": "No major risk", "severity": "low"},
                facts=["Cycle time has historical data."],
                interpretation=["Historical data is available."],
                recommendations=["Continue monitoring."],
                data_gaps=["cycle_time"],
            ).model_dump_json()

    context = AIContext(
        project="TEST",
        source="jira",
        analysis_window_days=14,
        metrics={
            "cycle_time": {
                "value": 3.0,
                "data_quality": {"status": "good"},
            }
        },
        historical={
            "cycle_time": {"values": [2.0, 3.0]}
        },
        insights=[],
        data_gaps=[],
    )

    result = AIAnalyzer(FakeProvider()).analyze(context)

    assert result["analysis"]["data_gaps"] == []

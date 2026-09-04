from app.ai.analyzer import AIAnalyzer
from app.ai.context import AIContext
from app.ai.ollama import OllamaProvider

class FakeProvider:
    model = "fake-model"
    def analyze(self, context, prompt):
        assert context.project == "KAN"
        assert '"value": 9' in prompt
        assert '"value": null' in prompt
        return "The main risk is WIP accumulation."

def test_analyzer_uses_context():
    context = AIContext(
        project="KAN", source="jira", analysis_window_days=14,
        metrics={"wip": {"value": 9}, "cycle_time": {"value": None}},
        historical={}, insights=[],
    )
    result = AIAnalyzer(FakeProvider()).analyze(context)
    assert result["answer"] == "The main risk is WIP accumulation."
    assert result["model"] == "fake-model"

def test_ollama_provider_sends_chat_request(monkeypatch):
    captured = {}
    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "WIP is the main risk."}}
    def fake_post(url, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse()
    monkeypatch.setattr("app.ai.ollama.requests.post", fake_post)

    context = AIContext(
        project="KAN", source="jira", analysis_window_days=14,
        metrics={}, historical={}, insights=[],
    )
    result = OllamaProvider(
        base_url="http://ollama.test", model="test-model", timeout=30
    ).analyze(context, "Analyze this context.")

    assert result == "WIP is the main risk."
    assert captured["url"] == "http://ollama.test/api/chat"
    assert captured["json"]["model"] == "test-model"
    assert captured["json"]["stream"] is False
    assert captured["timeout"] == 30

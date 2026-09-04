import json
from app.ai.context import AIContext
from app.ai.provider import AIProvider

class AIAnalyzer:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    def analyze(self, context: AIContext) -> dict:
        answer = self.provider.analyze(
            context=context,
            prompt=self._build_prompt(context),
        )
        return {
            "project": context.project,
            "source": context.source,
            "analysis_window_days": context.analysis_window_days,
            "model": getattr(self.provider, "model", None),
            "answer": answer,
        }

    @staticmethod
    def _build_prompt(context: AIContext) -> str:
        context_json = json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
        return (
            "Review the following delivery context and answer three questions:\n"
            "1. What is the most important delivery risk right now?\n"
            "2. What evidence supports that conclusion?\n"
            "3. What should the delivery manager pay attention to next?\n\n"
            "Do not invent information. Treat null values and insufficient_data "
            "as unavailable evidence. Clearly distinguish facts, interpretation, "
            "and recommendations.\n\n"
            "DELIVERY CONTEXT:\n" + context_json
        )

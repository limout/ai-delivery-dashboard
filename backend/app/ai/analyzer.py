import json

from pydantic import BaseModel, Field

from app.ai.context import AIContext
from app.ai.provider import AIProvider


class AIRisk(BaseModel):
    title: str
    severity: str


class AIStructuredResponse(BaseModel):
    risk: AIRisk
    facts: list[str] = Field(default_factory=list)
    interpretation: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class AIAnalyzer:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    def analyze(self, context: AIContext) -> dict:
        raw_answer = self.provider.analyze(
            context=context,
            prompt=self._build_prompt(context),
        )

        structured = self._parse_response(raw_answer)

        return {
            "project": context.project,
            "source": context.source,
            "analysis_window_days": context.analysis_window_days,
            "model": getattr(self.provider, "model", None),
            "analysis": structured.model_dump(mode="json"),
        }

    @staticmethod
    def _build_prompt(context: AIContext) -> str:
        context_json = json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )

        return (
            "You are an AI delivery intelligence assistant.\n\n"
            "Analyze ONLY the supplied delivery context.\n"
            "Do not invent metrics, events, causes, blockers, or other facts.\n\n"
            "IMPORTANT DATA RULES:\n"
            "- Values calculated by the metric engine are authoritative facts.\n"
            "- If a metric has data_quality.status = 'good', treat that metric "
            "as valid evidence. Do not call it unreliable or insufficient merely "
            "because the value looks surprising.\n"
            "- A value of 0 is a valid value when data_quality.status is 'good'.\n"
            "- A metric with value = null or data_quality.status = "
            "'insufficient_data' must be treated as unavailable evidence.\n"
            "- Do not recommend collecting data for a metric that already has "
            "data_quality.status = 'good'.\n"
            "- Historical points containing null values are unavailable evidence "
            "for that point; do not replace null with an estimated value.\n"
            "- Distinguish observed facts from interpretation and recommendations.\n"
            "- Only mention specific work items when they are present in the "
            "supplied evidence.\n\n"
            "Return ONLY valid JSON. Do not use Markdown or code fences.\n"
            "Use exactly this structure:\n"
            "{\n"
            '  "risk": {"title": "string", "severity": "low|medium|high"},\n'
            '  "facts": ["string"],\n'
            '  "interpretation": ["string"],\n'
            '  "recommendations": ["string"],\n'
            '  "data_gaps": ["string"]\n'
            "}\n\n"
            "Field rules:\n"
            "- risk: the single most important current delivery risk.\n"
            "- facts: directly observed/calculated evidence from the context only.\n"
            "- interpretation: cautious reasoning based on those facts. Do not "
            "state a possible cause as a confirmed fact.\n"
            "- recommendations: practical actions for the delivery manager that "
            "follow from the evidence.\n"
            "- data_gaps: only genuinely unavailable metrics/data. Use an empty "
            "array when there are no relevant gaps.\n\n"
            "DELIVERY CONTEXT:\n" + context_json
        )

    @staticmethod
    def _parse_response(raw_answer: str) -> AIStructuredResponse:
        text = raw_answer.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI provider returned a non-JSON response"
            ) from exc

        return AIStructuredResponse.model_validate(payload)

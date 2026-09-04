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

            "Your task is to reason over an already analyzed delivery context.\n"
            "The deterministic delivery layer has already calculated metrics, "
            "historical trends, and delivery insights.\n\n"

            "DATA AUTHORITY RULES:\n"
            "- Current values in 'metrics' are authoritative measurements.\n"
            "- Historical values in 'historical' are authoritative observations.\n"
            "- 'insights[].evidence' is authoritative structured evidence for "
            "the corresponding insight.\n"
            "- Treat deterministic evidence as more authoritative than your "
            "own assumptions.\n"
            "- Do not recalculate or reinterpret metric values.\n"
            "- A value of 0 is a valid value when its data quality is 'good'.\n"
            "- A metric with value = null or data_quality.status = "
            "'insufficient_data' is unavailable evidence.\n"
            "- Never describe unavailable data as if it were observed.\n"
            "- Do not treat sample size as a data quality problem when "
            "data_quality.status = 'good'.\n"
            "- Do not add a metric to data_gaps merely because its sample size "
            "is smaller than another metric.\n"
            "- If a metric has data_quality.status = 'good', do not describe "
            "that metric as having limited or insufficient data.\n\n"

            "REASONING RULES:\n"
            "- Separate facts, interpretation, and recommendations.\n"
            "- A fact must be directly supported by the supplied context.\n"
            "- An interpretation may connect multiple observed facts, but must "
            "remain cautious.\n"
            "- Do not claim a root cause unless the supplied data establishes it.\n"
            "- A blocker, process problem, team problem, or other cause must not "
            "be presented as confirmed unless explicitly supported by the data.\n"
            "- When the data shows a risk but does not establish its cause, "
            "say that the cause is not established by the available data.\n"
            "- Use historical trends when deciding whether a current signal "
            "represents deterioration or improvement.\n"
            "- Recommendations must be directly actionable from available "
            "evidence. Do not recommend investigating hypothetical causes "
            "unless the recommendation is explicitly framed as a validation step.\n"
            "- Do not recommend collecting data for a metric that already has "
            "data_quality.status = 'good'.\n"
            "- Only mention specific work items when they appear in the supplied "
            "evidence.\n\n"

            "IMPORTANT:\n"
            "The deterministic Insight Engine may already provide a signal and "
            "recommendation. You may refine their wording, but you must not "
            "turn an unproven explanation into a confirmed fact.\n\n"

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

        if not isinstance(payload, dict):
            raise ValueError(
                "AI provider returned JSON with an invalid top-level structure"
            )

        for field in (
            "facts",
            "interpretation",
            "recommendations",
            "data_gaps",
        ):
            value = payload.get(field)

            if isinstance(value, str):
                payload[field] = [value]
            elif value is None:
                payload[field] = []

        return AIStructuredResponse.model_validate(payload)
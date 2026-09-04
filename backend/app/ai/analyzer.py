from __future__ import annotations

import json

from app.ai.context import AIContext
from app.ai.provider import AIProvider
from app.ai.response import AIStructuredResponse
from app.ai.validator import AIResponseValidator


class AIAnalyzer:
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.validator = AIResponseValidator()

    def analyze(self, context: AIContext) -> dict:
        raw_answer = self.provider.analyze(
            context=context,
            prompt=self._build_prompt(context),
        )

        structured = self._parse_response(raw_answer)

        self.validator.validate(
            response=structured,
            context=context,
        )

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
            "- 'insights[].evidence' is authoritative structured evidence.\n"
            "- Treat deterministic evidence as more authoritative than your "
            "own assumptions.\n"
            "- Do not recalculate or reinterpret metric values.\n"
            "- A value of 0 is a valid value when its data quality is 'good'.\n"
            "- A metric with value = null or data_quality.status = "
            "'insufficient_data' is unavailable evidence.\n"
            "- Never describe unavailable data as if it were observed.\n"
            "- Never mention sample size as a data gap.\n"
            "- If data_quality.status = 'good', never describe that metric "
            "as limited, insufficient, incomplete, or unreliable.\n"
            "- data_gaps may contain only genuinely unavailable metrics.\n\n"
            "REASONING RULES:\n"
            "- Separate facts, interpretation, and recommendations.\n"
            "- Facts must be directly supported by the supplied context.\n"
            "- Keep facts atomic. Do not combine facts with interpretation.\n"
            "- Interpretation may connect multiple observed facts, but must "
            "remain cautious.\n"
            "- Do not claim a root cause unless the supplied data establishes it.\n"
            "- Do not present a possible cause as a confirmed fact.\n"
            "- When the data shows a risk but does not establish its cause, "
            "explicitly say that the cause is not established.\n"
            "- Recommendations must follow from available evidence.\n"
            "- Recommendations may propose validation steps for unconfirmed "
            "causes, but must not present those causes as facts.\n"
            "- Only mention specific work items when they appear in supplied "
            "evidence.\n\n"
            "OUTPUT RULES:\n"
            "- Return ONLY valid JSON.\n"
            "- Do not use Markdown.\n"
            "- Do not invent a different JSON structure.\n"
            "- Do not return summary/detailed_analysis or any other schema.\n"
            "- The response MUST contain exactly these top-level fields: "
            "risk, facts, interpretation, recommendations, data_gaps.\n\n"
            "Use exactly this structure:\n"
            "{\n"
            '  "risk": {"title": "string", "severity": "low|medium|high"},\n'
            '  "facts": ["string"],\n'
            '  "interpretation": ["string"],\n'
            '  "recommendations": ["string"],\n'
            '  "data_gaps": ["string"]\n'
            "}\n\n"
            "FIELD RULES:\n"
            "- risk: the single most important current delivery risk.\n"
            "- facts: directly observed/calculated evidence only.\n"
            "- interpretation: cautious reasoning based on facts.\n"
            "- recommendations: practical actions for the delivery manager.\n"
            "- data_gaps: only unavailable metrics/data.\n"
            "- Use an empty data_gaps array when there are no relevant gaps.\n\n"
            "DELIVERY CONTEXT:\n"
            + context_json
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

        expected_fields = {
            "risk",
            "facts",
            "interpretation",
            "recommendations",
            "data_gaps",
        }

        if not expected_fields.issubset(payload.keys()):
            raise ValueError(
                "AI provider returned JSON with an invalid response schema"
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

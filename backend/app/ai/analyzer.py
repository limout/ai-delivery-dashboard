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
        prompt = self._build_prompt(context)
        raw_answer = self.provider.analyze(
            context=context,
            prompt=prompt,
        )

        structured = self._parse_response(raw_answer)

        # data_gaps are deterministic backend output. Normalize the LLM
        # response before validation so the validator checks only the
        # authoritative value.
        authoritative_gaps = (
            list(context.data_gaps)
            or AIResponseValidator._derive_data_gaps(context)
        )
        structured.data_gaps = authoritative_gaps

        try:
            self.validator.validate(
                response=structured,
                context=context,
            )
        except ValueError as exc:
            error = str(exc)

            if error.startswith("AI response references unknown work item"):
                retry_prompt = self._build_work_item_retry_prompt(
                    context=context,
                    validation_error=error,
                )
            elif error.startswith("AI response reports an unsupported data gap"):
                retry_prompt = self._build_data_gap_retry_prompt(
                    context=context,
                    validation_error=error,
                )
            else:
                raise

            retry_answer = self.provider.analyze(
                context=context,
                prompt=retry_prompt,
            )
            structured = self._parse_response(retry_answer)
            structured.data_gaps = authoritative_gaps
            self.validator.validate(
                response=structured,
                context=context,
            )

        analysis = structured.model_dump(mode="json")

        # data_gaps are deterministic backend output. The LLM must not be
        # allowed to infer, add, or remove them.
        analysis["data_gaps"] = authoritative_gaps

        return {
            "project": context.project,
            "source": context.source,
            "analysis_window_days": context.analysis_window_days,
            "model": getattr(self.provider, "model", None),
            "analysis": analysis,
        }

    @staticmethod
    def _build_prompt(context: AIContext) -> str:
        context_json = json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )

        available_metrics = []
        unavailable_metrics = list(context.data_gaps)

        for metric_name, metric in context.metrics.items():
            if metric_name in context.data_gaps:
                continue

            if not isinstance(metric, dict):
                continue

            data_quality = metric.get("data_quality")
            if (
                isinstance(data_quality, dict)
                and data_quality.get("status") == "good"
                and metric.get("value") is not None
            ):
                available_metrics.append(metric_name)

        available_metrics_text = (
            ", ".join(available_metrics)
            if available_metrics
            else "none"
        )
        unavailable_metrics_text = (
            ", ".join(unavailable_metrics)
            if unavailable_metrics
            else "none"
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
            "- 'data_gaps' in the supplied context is authoritative. It is "
            "computed by the deterministic layer, not by the LLM.\n"
            "- Treat deterministic evidence as more authoritative than your "
            "own assumptions.\n"
            "- Do not recalculate or reinterpret metric values.\n"
            "- A value of 0 is a valid value when its data quality is 'good'.\n"
            "- A metric with value = null or data_quality.status = "
            "'insufficient_data' is unavailable evidence.\n"
            "- Never describe unavailable data as if it were observed.\n"
            "- Never mention sample size as a data gap.\n"
            "- If data_quality.status = 'good', never describe that metric "
            "as limited, insufficient, incomplete, or unreliable.\n\n"
            "DATA AVAILABILITY:\n"
            f"- AVAILABLE METRICS: {available_metrics_text}\n"
            f"- DETERMINISTIC DATA GAPS: {unavailable_metrics_text}\n"
            "- data_gaps MUST contain only metrics from DETERMINISTIC DATA GAPS.\n"
            "- Do not add other missing metrics such as defect rate, team "
            "capacity, or sample size unless they are explicitly present in "
            "DETERMINISTIC DATA GAPS.\n"
            "- If DETERMINISTIC DATA GAPS is 'none', data_gaps MUST be an "
            "empty array.\n"
            "- Historical data marked available in 'historical' MUST NOT be "
            "described as missing.\n"
            "- In particular, if historical velocity contains iteration points, "
            "historical velocity is available for trend analysis.\n\n"
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
            "- data_gaps: reproduce only the genuinely unavailable metrics "
            "from DETERMINISTIC DATA GAPS.\n"
            "- Do not use data_gaps for potentially useful but currently "
            "unimplemented metrics.\n\n"
            "UNIT AND SEMANTIC RULES:\n"
            "- Never change or invent the unit of a metric.\n"
            "- If a metric unit is story_points, refer to Story Points, not "
            "work items or tasks.\n"
            "- The commitment_vs_completed metric is measured in percent and "
            "its committed/completed values are Story Points.\n"
            "- Therefore, never describe commitment_vs_completed as a percentage "
            "of committed work items. Describe it as a percentage of committed "
            "Story Points completed.\n"
            "- If discussing velocity, use Story Points per iteration.\n"
            "- If discussing WIP or throughput with unit items, work items/tasks "
            "are appropriate terms.\n\n"
            "WORK ITEM REFERENCE RULES:\n"
            "- Work item IDs may be referenced only when they appear in the supplied insight evidence.\n"
            "- Never invent, guess, or construct a work item ID.\n"
            "- If an ID is not present in evidence, do not mention it.\n\n"
            "DELIVERY CONTEXT:\n"
            + context_json
        )

    @classmethod
    def _build_work_item_retry_prompt(
        cls,
        context: AIContext,
        validation_error: str,
    ) -> str:
        known_ids = sorted(
            AIResponseValidator._known_work_item_ids(context)
        )
        allowed_ids = ", ".join(known_ids) if known_ids else "none"

        return (
            cls._build_prompt(context)
            + "\n\nCORRECTION REQUIRED:\n"
            + f"The previous AI response failed validation: {validation_error}.\n"
            + f"AUTHORITATIVE WORK ITEM IDS: {allowed_ids}\n"
            + "You may reference a work item ID only if it appears in this list.\n"
            + "Never invent, guess, or construct a work item ID.\n"
            + "If no valid work item ID supports a statement, describe the statement without an ID.\n"
            + "Regenerate the complete response and return ONLY valid JSON matching the required schema.\n"
        )

    @classmethod
    def _build_data_gap_retry_prompt(
        cls,
        context: AIContext,
        validation_error: str,
    ) -> str:
        authoritative_gaps = sorted(set(context.data_gaps))
        allowed_gaps = ", ".join(authoritative_gaps) if authoritative_gaps else "none"

        return (
            cls._build_prompt(context)
            + "\n\nCORRECTION REQUIRED:\n"
            + f"The previous AI response failed validation: {validation_error}.\n"
            + f"AUTHORITATIVE DATA GAPS: {allowed_gaps}\n"
            + "The data_gaps field may contain ONLY metrics from this authoritative list.\n"
            + "Do not add cycle_time or any other metric unless it appears in the authoritative list.\n"
            + "Historical data being absent or different from current metrics does not by itself create a data gap.\n"
            + "If AUTHORITATIVE DATA GAPS is 'none', return an empty data_gaps array.\n"
            + "Regenerate the complete response and return ONLY valid JSON matching the required schema.\n"
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

from __future__ import annotations

import re

from app.ai.context import AIContext
from app.ai.response import AIStructuredResponse


class AIResponseValidator:
    """
    Validate an AI response against deterministic delivery context.

    The LLM is not treated as the source of truth. Deterministic metrics,
    historical data and structured insight evidence remain authoritative.
    """

    WORK_ITEM_PATTERN = re.compile(r"\b[A-Z][A-Z0-9_]*-\d+\b")

    def validate(
        self,
        response: AIStructuredResponse,
        context: AIContext,
    ) -> AIStructuredResponse:
        self._validate_data_gaps(response, context)
        self._validate_work_item_references(response, context)
        return response

    @staticmethod
    def _validate_data_gaps(
        response: AIStructuredResponse,
        context: AIContext,
    ) -> None:
        for gap in response.data_gaps:
            normalized_gap = gap.lower()

            for metric_name, metric in context.metrics.items():
                metric_label = metric_name.lower().replace("_", " ")

                if metric_label not in normalized_gap:
                    continue

                if not isinstance(metric, dict):
                    continue

                data_quality = metric.get("data_quality")
                if not isinstance(data_quality, dict):
                    continue

                if data_quality.get("status") == "good":
                    raise ValueError(
                        f"AI response incorrectly reports '{metric_name}' "
                        "as a data gap although data quality is good"
                    )

    def _validate_work_item_references(
        self,
        response: AIStructuredResponse,
        context: AIContext,
    ) -> None:
        known_ids = self._known_work_item_ids(context)

        texts = [
            response.risk.title,
            *response.facts,
            *response.interpretation,
            *response.recommendations,
        ]

        for text in texts:
            for item_id in self.WORK_ITEM_PATTERN.findall(text):
                if item_id.upper() not in known_ids:
                    raise ValueError(
                        f"AI response references unknown work item '{item_id}'"
                    )

    @classmethod
    def _known_work_item_ids(cls, context: AIContext) -> set[str]:
        known_ids: set[str] = set()

        for insight in context.insights:
            if not isinstance(insight, dict):
                continue

            evidence = insight.get("evidence")
            if not isinstance(evidence, dict):
                continue

            cls._collect_ids_from_value(evidence, known_ids)

        return known_ids

    @classmethod
    def _collect_ids_from_value(
        cls,
        value,
        known_ids: set[str],
    ) -> None:
        if isinstance(value, dict):
            item_id = value.get("id")
            if isinstance(item_id, str):
                known_ids.add(item_id.upper())

            for child in value.values():
                cls._collect_ids_from_value(child, known_ids)

        elif isinstance(value, list):
            for child in value:
                cls._collect_ids_from_value(child, known_ids)

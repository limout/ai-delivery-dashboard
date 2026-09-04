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
        self._validate_metric_units(response, context)
        return response

    @staticmethod
    def _validate_metric_units(
        response: AIStructuredResponse,
        context: AIContext,
    ) -> None:
        commitment_metric = context.metrics.get("commitment_vs_completed")
        if not isinstance(commitment_metric, dict):
            return

        texts = [
            response.risk.title,
            *response.facts,
            *response.interpretation,
            *response.recommendations,
        ]

        for text in texts:
            normalized = text.lower()
            if "committed work items" in normalized:
                raise ValueError(
                    "AI response changes commitment_vs_completed unit: "
                    "committed/completed values are Story Points, not work items"
                )

    @staticmethod
    def _validate_data_gaps(
        response: AIStructuredResponse,
        context: AIContext,
    ) -> None:
        deterministic_gaps = context.data_gaps or AIResponseValidator._derive_data_gaps(
            context
        )

        def normalize_metric_name(value: str) -> str:
            return value.lower().strip().replace("_", " ")

        expected_gaps = {
            normalize_metric_name(metric_name)
            for metric_name in deterministic_gaps
        }

        actual_gaps: set[str] = set()

        for gap in response.data_gaps:
            normalized_gap = normalize_metric_name(gap)
            matched_expected = False

            for expected_gap in expected_gaps:
                if expected_gap in normalized_gap:
                    matched_expected = True
                    actual_gaps.add(expected_gap)
                    break

            if not matched_expected:
                for metric_name, metric in context.metrics.items():
                    metric_label = normalize_metric_name(metric_name)
                    if metric_label in normalized_gap:
                        data_quality = metric.get("data_quality")
                        if (
                            isinstance(data_quality, dict)
                            and data_quality.get("status") == "good"
                        ):
                            raise ValueError(
                                f"AI response incorrectly reports '{metric_name}' "
                                "as a data gap although data quality is good"
                            )
                raise ValueError(
                    f"AI response reports an unsupported data gap: '{gap}'"
                )

        missing_gaps = expected_gaps - actual_gaps
        if missing_gaps:
            missing = ", ".join(sorted(missing_gaps))
            raise ValueError(
                "AI response omitted deterministic data gaps: "
                f"{missing}"
            )

    @staticmethod
    def _derive_data_gaps(context: AIContext) -> list[str]:
        """Derive unavailable current metrics when the context has no explicit list.

        This preserves compatibility with older callers/tests while the
        AIContextBuilder remains the preferred source of deterministic gaps.
        """
        gaps: list[str] = []

        for metric_name, metric in context.metrics.items():
            if not isinstance(metric, dict):
                continue

            value = metric.get("value")
            data_quality = metric.get("data_quality")

            if not isinstance(data_quality, dict):
                continue

            if data_quality.get("status") == "insufficient_data" or value is None:
                gaps.append(metric_name)

        return gaps

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

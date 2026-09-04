from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AIContext(BaseModel):
    """Structured, factual delivery context supplied to an AI model."""

    project: str
    source: str
    analysis_window_days: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    historical: dict[str, Any] = Field(default_factory=dict)
    insights: list[dict[str, Any]] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class AIContextBuilder:
    """Build an AI-ready context from deterministic delivery analysis.

    This class does not calculate delivery metrics or call an LLM. It packages
    deterministic analysis and derives the authoritative list of unavailable
    current metrics for the AI layer.
    """

    def build(self, analysis: dict[str, Any], source: str) -> AIContext:
        metrics = self._copy_dict(analysis.get("metrics"))
        historical = self._copy_dict(analysis.get("historical"))

        return AIContext(
            project=str(analysis.get("project", "")),
            source=source,
            analysis_window_days=int(analysis.get("days", 0)),
            metrics=metrics,
            historical=historical,
            insights=self._copy_insights(analysis.get("insights")),
            data_gaps=self._build_data_gaps(metrics),
        )

    @staticmethod
    def _copy_dict(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        return dict(value)

    @staticmethod
    def _copy_insights(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        result = []
        for insight in value:
            if isinstance(insight, dict):
                result.append(dict(insight))
        return result

    @staticmethod
    def _build_data_gaps(metrics: dict[str, Any]) -> list[str]:
        """Return only metrics that deterministic data quality marks unavailable."""
        gaps: list[str] = []

        for metric_name, metric in metrics.items():
            if not isinstance(metric, dict):
                continue

            value = metric.get("value")
            data_quality = metric.get("data_quality")

            if not isinstance(data_quality, dict):
                continue

            if data_quality.get("status") == "insufficient_data" or value is None:
                gaps.append(metric_name)

        return gaps

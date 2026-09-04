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


class AIContextBuilder:
    """Build an AI-ready context from the existing deterministic analysis result.

    This class deliberately does not calculate metrics, infer new facts, or
    call an LLM. It only packages data already produced by the dashboard.
    """

    def build(
        self,
        analysis: dict[str, Any],
        source: str,
    ) -> AIContext:
        return AIContext(
            project=str(analysis.get("project", "")),
            source=source,
            analysis_window_days=int(analysis.get("days", 0)),
            metrics=self._copy_dict(analysis.get("metrics")),
            historical=self._copy_dict(analysis.get("historical")),
            insights=self._copy_insights(analysis.get("insights")),
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

        result: list[dict[str, Any]] = []

        for insight in value:
            if isinstance(insight, dict):
                result.append(dict(insight))

        return result

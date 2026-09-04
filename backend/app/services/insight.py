from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Insight:
    id: str
    severity: str
    title: str
    fact: str
    signal: str
    recommendation: str
    confidence: str
    metric: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "fact": self.fact,
            "signal": self.signal,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metric": self.metric,
        }


class InsightEngine:
    """Deterministic delivery-risk rules.

    The engine deliberately does not use an LLM. It converts measured data into
    explicit facts, signals, and recommendations that can later be passed to AI.
    """

    def analyze(
        self,
        metrics: dict[str, dict[str, Any]],
        historical: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, str]]:
        historical = historical or {}
        insights: list[Insight] = []

        self._check_wip_congestion(metrics, historical, insights)
        self._check_cycle_time_slowdown(metrics, historical, insights)
        self._check_bottleneck_risk(metrics, insights)
        self._check_flow_deterioration(metrics, historical, insights)
        self._check_planning_risk(metrics, insights)

        severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
        insights.sort(key=lambda item: severity_order.get(item.severity, 99))
        return [item.to_dict() for item in insights]

    def _check_wip_congestion(self, metrics, historical, insights):
        wip = self._value(metrics, "wip")
        throughput = self._value(metrics, "throughput")
        wip_change = self._trend(historical.get("wip"))
        throughput_change = self._trend(historical.get("throughput"))

        if wip is None or throughput is None:
            return

        if wip_change > 0 and throughput_change <= 0:
            insights.append(
                Insight(
                    id="wip-congestion",
                    severity="high",
                    title="WIP is increasing without higher throughput",
                    fact=f"WIP is {wip:g}; WIP is trending up while throughput is flat or declining.",
                    signal="The delivery system may be accumulating work faster than it finishes it.",
                    recommendation="Review aging or blocked work and consider reducing new work entering the system.",
                    confidence="medium",
                    metric="wip",
                )
            )

    def _check_cycle_time_slowdown(self, metrics, historical, insights):
        cycle_time = self._value(metrics, "cycle_time")
        change = self._trend(historical.get("cycle_time"))
        if cycle_time is None or change <= 0:
            return

        insights.append(
            Insight(
                id="cycle-time-slowdown",
                severity="medium",
                title="Cycle Time is increasing",
                fact=f"Current Cycle Time is {cycle_time:g} days and the historical trend is upward.",
                signal="Completed work is taking longer to move through the delivery process.",
                recommendation="Inspect recent completed items for blockers, handoffs, or unusually large work.",
                confidence="medium",
                metric="cycle_time",
            )
        )

    def _check_bottleneck_risk(self, metrics, insights):
        wip = self._value(metrics, "wip")
        throughput = self._value(metrics, "throughput")
        if wip is None or throughput is None or throughput <= 0:
            return

        ratio = wip / throughput
        if ratio >= 2:
            insights.append(
                Insight(
                    id="wip-throughput-bottleneck",
                    severity="medium",
                    title="WIP is high relative to throughput",
                    fact=f"There are {wip:g} WIP items against throughput of {throughput:g} in the current metric window.",
                    signal="The current work inventory is large compared with the rate at which work is completed.",
                    recommendation="Prioritize finishing existing work before starting additional items.",
                    confidence="medium",
                    metric="wip",
                )
            )

    def _check_flow_deterioration(self, metrics, historical, insights):
        """Detect simultaneous deterioration in WIP and Cycle Time.

        This is a stronger signal than either trend alone: more work is
        accumulating while completed work is also taking longer to flow.
        """
        wip = self._value(metrics, "wip")
        cycle_time = self._value(metrics, "cycle_time")
        wip_change = self._trend(historical.get("wip"))
        cycle_change = self._trend(historical.get("cycle_time"))

        if (
            wip is None
            or cycle_time is None
            or wip_change <= 0
            or cycle_change <= 0
        ):
            return

        insights.append(
            Insight(
                id="flow-deterioration",
                severity="high",
                title="Flow is deteriorating",
                fact=(
                    f"WIP is {wip:g} and Cycle Time is {cycle_time:g} days; "
                    "both historical trends are increasing."
                ),
                signal=(
                    "More work is accumulating while completed work is also "
                    "taking longer to move through the system."
                ),
                recommendation=(
                    "Prioritize the oldest active work, investigate blockers "
                    "and avoid increasing work entering the system until flow improves."
                ),
                confidence="high",
                metric="wip",
            )
        )

    def _check_planning_risk(self, metrics, insights):
        completion = self._value(metrics, "commitment_vs_completed")
        if completion is None or completion >= 70:
            return

        severity = "high" if completion < 50 else "medium"
        insights.append(
            Insight(
                id="planning-risk",
                severity=severity,
                title="Commitment completion is low",
                fact=f"Average completed commitment is {completion:g}%.",
                signal="Recent iterations are completing substantially less than their committed scope.",
                recommendation="Review spillover and scope changes before increasing future commitments.",
                confidence="medium",
                metric="commitment_vs_completed",
            )
        )

    @staticmethod
    def _value(metrics: dict[str, dict[str, Any]], name: str) -> float | None:
        metric = metrics.get(name)
        if not metric:
            return None
        value = metric.get("value")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _trend(data: dict[str, Any] | None) -> float:
        if not data:
            return 0.0
        points = data.get("points", [])
        values = [p.get("value") for p in points if p.get("value") is not None]
        if len(values) < 2:
            return 0.0
        return float(values[-1]) - float(values[0])

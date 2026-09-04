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
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "fact": self.fact,
            "signal": self.signal,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "metric": self.metric,
            "evidence": self.evidence,
        }


class InsightEngine:
    """Deterministic delivery-risk rules used as an AI-ready baseline.

    The engine does not pretend to be the AI layer. It turns measured metrics
    and historical movement into explicit, traceable signals. Later, an LLM can
    reason over the same facts and evidence instead of recalculating metrics.
    """

    def analyze(
        self,
        metrics: dict[str, dict[str, Any]],
        historical: dict[str, dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        historical = historical or {}
        insights: list[Insight] = []

        flow_deteriorating = self._has_flow_deterioration(
            metrics, historical
        )

        if not flow_deteriorating:
            self._check_wip_congestion(metrics, historical, insights)

        self._check_flow_deterioration(metrics, historical, insights)
        self._check_bottleneck_risk(metrics, insights)
        self._check_throughput_decline(metrics, historical, insights)
        self._check_cycle_time_slowdown(metrics, historical, insights)
        self._check_lead_time_slowdown(metrics, historical, insights)
        self._check_velocity_decline(metrics, historical, insights)
        self._check_planning_risk(metrics, insights)

        severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
        insights.sort(key=lambda item: severity_order.get(item.severity, 99))

        return [item.to_dict() for item in insights]

    def _check_wip_congestion(self, metrics, historical, insights):
        wip = self._value(metrics, "wip")
        throughput = self._value(metrics, "throughput")
        wip_change = self._trend(historical.get("wip"))
        throughput_change = self._trend(historical.get("throughput"))

        if (
            wip is None
            or throughput is None
            or wip_change <= 0
            or throughput_change > 0
        ):
            return

        insights.append(
            Insight(
                id="wip-congestion",
                severity="high",
                title="WIP is increasing without higher throughput",
                fact=(
                    f"WIP is {wip:g}; WIP is trending up while throughput "
                    "is flat or declining."
                ),
                signal=(
                    "The delivery system may be accumulating work faster "
                    "than it finishes it."
                ),
                recommendation=(
                    "Review aging or blocked work and consider reducing "
                    "new work entering the system."
                ),
                confidence="medium",
                metric="wip",
                evidence={
                    "wip": {
                        "current": wip,
                        "trend": wip_change,
                    },
                    "throughput": {
                        "current": throughput,
                        "trend": throughput_change,
                    },
                },
            )
        )

    def _has_flow_deterioration(self, metrics, historical) -> bool:
        return (
            self._value(metrics, "wip") is not None
            and self._value(metrics, "cycle_time") is not None
            and self._trend(historical.get("wip")) > 0
            and self._trend(historical.get("cycle_time")) > 0
        )

    def _check_flow_deterioration(self, metrics, historical, insights):
        wip = self._value(metrics, "wip")
        cycle_time = self._value(metrics, "cycle_time")

        if not self._has_flow_deterioration(metrics, historical):
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
                evidence={
                    "wip": {
                        "current": wip,
                        "trend": self._trend(historical.get("wip")),
                    },
                    "cycle_time": {
                        "current": cycle_time,
                        "trend": self._trend(historical.get("cycle_time")),
                    },
                },
            )
        )

    def _check_bottleneck_risk(self, metrics, insights):
        wip = self._value(metrics, "wip")
        throughput = self._value(metrics, "throughput")

        if wip is None or throughput is None or throughput <= 0:
            return

        ratio = wip / throughput
        if ratio < 2:
            return

        insights.append(
            Insight(
                id="wip-throughput-bottleneck",
                severity="medium",
                title="WIP is high relative to throughput",
                fact=(
                    f"There are {wip:g} WIP items against throughput of "
                    f"{throughput:g} in the current metric window."
                ),
                signal=(
                    "The current work inventory is large compared with "
                    "the rate at which work is completed."
                ),
                recommendation=(
                    "Prioritize finishing existing work before starting "
                    "additional items."
                ),
                confidence="medium",
                metric="wip",
                evidence={
                    "wip": {"current": wip},
                    "throughput": {"current": throughput},
                    "wip_to_throughput_ratio": ratio,
                },
            )
        )

    def _check_throughput_decline(self, metrics, historical, insights):
        throughput = self._value(metrics, "throughput")
        change = self._trend(historical.get("throughput"))

        if throughput is None or change >= 0:
            return

        insights.append(
            Insight(
                id="throughput-decline",
                severity="medium",
                title="Throughput is declining",
                fact=(
                    f"Current throughput is {throughput:g} completed items "
                    "and the historical trend is downward."
                ),
                signal=(
                    "The system is completing less work than earlier "
                    "in the selected period."
                ),
                recommendation=(
                    "Check whether blockers, aging work, or increased "
                    "work size are reducing completion rate."
                ),
                confidence="medium",
                metric="throughput",
                evidence={
                    "throughput": {
                        "current": throughput,
                        "trend": change,
                    }
                },
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
                fact=(
                    f"Current Cycle Time is {cycle_time:g} days and the "
                    "historical trend is upward."
                ),
                signal=(
                    "Completed work is taking longer to move through "
                    "the delivery process."
                ),
                recommendation=(
                    "Inspect recent completed items for blockers, handoffs, "
                    "or unusually large work."
                ),
                confidence="medium",
                metric="cycle_time",
                evidence={
                    "cycle_time": {
                        "current": cycle_time,
                        "trend": change,
                    }
                },
            )
        )

    def _check_lead_time_slowdown(self, metrics, historical, insights):
        lead_time = self._value(metrics, "lead_time")
        change = self._trend(historical.get("lead_time"))

        if lead_time is None or change <= 0:
            return

        insights.append(
            Insight(
                id="lead-time-slowdown",
                severity="medium",
                title="Lead Time is increasing",
                fact=(
                    f"Current Lead Time is {lead_time:g} days and the "
                    "historical trend is upward."
                ),
                signal=(
                    "Work is taking longer from creation to completion, "
                    "indicating increasing end-to-end delivery latency."
                ),
                recommendation=(
                    "Inspect queue time, waiting states, handoffs, and aging "
                    "items before increasing incoming demand."
                ),
                confidence="medium",
                metric="lead_time",
                evidence={
                    "lead_time": {
                        "current": lead_time,
                        "trend": change,
                    }
                },
            )
        )

    def _check_velocity_decline(self, metrics, historical, insights):
        velocity = self._value(metrics, "velocity")
        change = self._trend(historical.get("velocity"))

        if velocity is None or change >= 0:
            return

        insights.append(
            Insight(
                id="velocity-decline",
                severity="medium",
                title="Velocity is declining",
                fact=(
                    f"Current average velocity is {velocity:g} Story Points "
                    "and the historical trend is downward."
                ),
                signal=(
                    "The team is completing fewer Story Points per iteration "
                    "than earlier iterations."
                ),
                recommendation=(
                    "Review spillover, blockers, scope changes, and unusually "
                    "large or complex work before changing commitments."
                ),
                confidence="medium",
                metric="velocity",
                evidence={
                    "velocity": {
                        "current": velocity,
                        "trend": change,
                    }
                },
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
                signal=(
                    "Recent iterations are completing substantially less "
                    "than their committed scope."
                ),
                recommendation=(
                    "Review spillover and scope changes before increasing "
                    "future commitments."
                ),
                confidence="medium",
                metric="commitment_vs_completed",
                evidence={
                    "commitment_vs_completed": {
                        "current": completion,
                    }
                },
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

        values = [
            p.get("value")
            for p in points
            if p.get("value") is not None
        ]

        if len(values) < 2:
            return 0.0

        return float(values[-1]) - float(values[0])
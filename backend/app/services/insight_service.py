from __future__ import annotations

from datetime import date, timedelta

from app.metrics.historical import HistoricalMetrics
from app.services.insight import InsightEngine


DEFAULT_INSIGHT_METRICS = [
    "wip",
    "throughput",
    "cycle_time",
    "lead_time",
    "velocity",
    "commitment_vs_completed",
]


class InsightService:
    def __init__(self, connector, metric_engine):
        self.connector = connector
        self.metric_engine = metric_engine
        self.insight_engine = InsightEngine()

    def analyze(
        self,
        project: str,
        metric_names: list[str] | None = None,
        historical_metric_names: list[str] | None = None,
        days: int = 14,
    ) -> dict:
        metric_names = metric_names or DEFAULT_INSIGHT_METRICS
        historical_metric_names = historical_metric_names or DEFAULT_INSIGHT_METRICS

        work_items = self.connector.get_work_items(project)

        history = []
        for item in work_items:
            history.extend(self.connector.get_work_item_history(item.id))

        metrics = self.metric_engine.calculate(
            work_items=work_items,
            history=history,
            metric_names=metric_names,
        )

        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        historical = HistoricalMetrics()
        historical_results = {}

        for metric_name in historical_metric_names:
            historical_results[metric_name] = historical.calculate(
                metric=metric_name,
                work_items=work_items,
                histories=history,
                start_date=start_date,
                end_date=end_date,
            )

        insights = self.insight_engine.analyze(
            metrics=metrics,
            historical=historical_results,
        )

        return {
            "project": project,
            "days": days,
            "metrics": metrics,
            "historical": historical_results,
            "insights": insights,
        }

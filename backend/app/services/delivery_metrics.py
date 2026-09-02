from app.core.connectors.base import DeliveryConnector
from app.metrics.engine import MetricEngine


class DeliveryMetricsService:
    def __init__(
        self,
        connector: DeliveryConnector,
        metric_engine: MetricEngine,
    ):
        self.connector = connector
        self.metric_engine = metric_engine

    def calculate(self, project: str, metric_names: list[str]) -> dict:
        work_items = self.connector.get_work_items(project)

        history = []

        for item in work_items:
            history.extend(
                self.connector.get_work_item_history(item.id)
            )

        results = self.metric_engine.calculate(
            work_items=work_items,
            history=history,
            metric_names=metric_names,
        )

        for name in metric_names:
            metric = self.metric_engine.registry.get(name)

            results[name]["category"] = metric.category
            results[name]["description"] = metric.description

        return results
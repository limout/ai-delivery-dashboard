from app.core.models.work_item import WorkItem
from app.metrics.registry import MetricRegistry


class MetricEngine:
    def __init__(self, registry: MetricRegistry):
        self.registry = registry

    def calculate(
        self,
        work_items: list[WorkItem],
        metric_names: list[str],
    ) -> dict:
        results = {}

        for name in metric_names:
            metric = self.registry.get(name)
            results[name] = metric.calculate(work_items)

        return results
from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.metrics.registry import MetricRegistry


class MetricEngine:
    def __init__(self, registry: MetricRegistry):
        self.registry = registry

    def calculate(
        self,
        work_items: list[WorkItem],
        history: list[WorkItemHistory],
        metric_names: list[str],
    ) -> dict:
        results = {}

        data_sources = {
            "work_items": work_items,
            "history": history,
        }

        for name in metric_names:
            metric = self.registry.get(name)

            data = data_sources.get(metric.required_data)

            if data is None:
                raise ValueError(
                    f"Unsupported data source: {metric.required_data}"
                )

            results[name] = metric.calculate(data)

        return results
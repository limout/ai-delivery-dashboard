from app.core.models.work_item import WorkItem
from app.metrics.base import Metric


class ThroughputMetric(Metric):
    name = "throughput"
    description = "Number of completed work items."
    category = "flow"

    def calculate(self, work_items: list[WorkItem]) -> dict:
        completed = [
            item
            for item in work_items
            if item.status == "Done"
        ]

        return {
            "metric": self.name,
            "value": len(completed),
            "unit": "items",
            "sample_size": len(work_items),
        }
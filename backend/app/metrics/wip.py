from app.core.models.work_item import WorkItem
from app.metrics.base import Metric


class WIPMetric(Metric):
    name = "wip"
    description = "Number of work items currently in progress."
    category = "snapshot"
    required_data = "work_items"

    def calculate(
        self,
        work_items: list[WorkItem],
    ) -> dict:
        wip_items = [
            item
            for item in work_items
            if item.status == "In Progress"
        ]

        return {
            "metric": self.name,
            "value": len(wip_items),
            "unit": "items",
            "sample_size": len(work_items),
        }
from app.core.models.work_item import WorkItem
from app.metrics.base import Metric
from app.metrics.data_quality import DataQuality


class WIPMetric(Metric):
    name = "wip"
    description = "Number of work items currently in progress."
    category = "snapshot"
    required_data = "work_items"

    def calculate(
        self,
        work_items: list[WorkItem],
    ) -> dict:
        if not work_items:
            quality = DataQuality(
                status="insufficient_data",
                message="No work items available.",
            )

            return {
                "metric": self.name,
                "value": None,
                "unit": "items",
                "sample_size": 0,
                "data_quality": quality.model_dump(),
            }

        wip_items = [
            item
            for item in work_items
            if item.status == "In Progress"
        ]

        quality = DataQuality(
            status="good",
            message="Sufficient data available.",
        )

        return {
            "metric": self.name,
            "value": len(wip_items),
            "unit": "items",
            "sample_size": len(work_items),
            "data_quality": quality.model_dump(),
        }
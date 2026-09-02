from app.core.models.work_item import WorkItem
from app.metrics.base import Metric
from app.metrics.data_quality import DataQuality


class ThroughputMetric(Metric):
    name = "throughput"
    description = "Number of completed work items."
    category = "flow"
    required_data = "work_items"

    def calculate(self, work_items: list[WorkItem]) -> dict:
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

        completed = [
            item
            for item in work_items
            if item.status == "Done"
        ]

        quality = DataQuality(
            status="good",
            message="Sufficient data available.",
        )

        return {
            "metric": self.name,
            "value": len(completed),
            "unit": "items",
            "sample_size": len(work_items),
            "data_quality": quality.model_dump(),
        }
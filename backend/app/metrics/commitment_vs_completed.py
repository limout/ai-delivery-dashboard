from app.core.models.work_item import WorkItem
from app.metrics.base import Metric


class CommitmentVsCompletedMetric(Metric):
    name = "commitment_vs_completed"
    description = "Committed Story Points versus completed Story Points per iteration."
    category = "planning"
    required_data = "work_items"

    def calculate(self, work_items: list[WorkItem]) -> dict:
        planning_items = [
            item
            for item in work_items
            if item.delivery_role.value == "planning_item"
        ]

        iterations: dict[str, dict[str, float]] = {}

        for item in planning_items:
            if not item.iteration:
                continue

            if item.iteration not in iterations:
                iterations[item.iteration] = {
                    "committed": 0.0,
                    "completed": 0.0,
                }

            if item.story_points is None:
                continue

            iterations[item.iteration]["committed"] += item.story_points

            if item.status == "Done":
                iterations[item.iteration]["completed"] += item.story_points

        if not iterations:
            return {
                "metric": self.name,
                "value": None,
                "unit": "percent",
                "sample_size": 0,
                "status": "insufficient_data",
                "message": "No iteration or Story Point data available.",
                "iterations": {},
            }

        valid_iterations = {
            name: data
            for name, data in iterations.items()
            if data["committed"] > 0
        }

        if not valid_iterations:
            return {
                "metric": self.name,
                "value": None,
                "unit": "percent",
                "sample_size": 0,
                "status": "insufficient_data",
                "message": "No iterations with committed Story Points.",
                "iterations": iterations,
            }

        percentages = []

        for data in valid_iterations.values():
            data["completion_percentage"] = round(
                data["completed"] / data["committed"] * 100,
                2,
            )
            percentages.append(data["completion_percentage"])

        average_completion = sum(percentages) / len(percentages)

        return {
            "metric": self.name,
            "value": round(average_completion, 2),
            "unit": "percent",
            "sample_size": len(valid_iterations),
            "status": "ok",
            "iterations": iterations,
        }
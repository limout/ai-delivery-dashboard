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
            and item.story_points is not None
            and item.iteration
        ]

        iterations: dict[str, dict[str, float]] = {}

        for item in planning_items:
            iteration = item.iteration
            assert iteration is not None

            iterations.setdefault(
                iteration,
                {"committed": 0.0, "completed": 0.0},
            )

            iterations[iteration]["committed"] += item.story_points

            if item.status == "Done":
                iterations[iteration]["completed"] += item.story_points

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

        percentages = []

        for data in iterations.values():
            if data["committed"] <= 0:
                continue

            data["completion_percentage"] = round(
                data["completed"] / data["committed"] * 100,
                2,
            )
            percentages.append(data["completion_percentage"])

        if not percentages:
            return {
                "metric": self.name,
                "value": None,
                "unit": "percent",
                "sample_size": 0,
                "status": "insufficient_data",
                "message": "No iterations with committed Story Points.",
                "iterations": iterations,
            }

        average_completion = sum(percentages) / len(percentages)

        return {
            "metric": self.name,
            "value": round(average_completion, 2),
            "unit": "percent",
            "sample_size": len(percentages),
            "status": "ok",
            "iterations": iterations,
        }

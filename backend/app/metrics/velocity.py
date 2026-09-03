from app.core.models.work_item import WorkItem
from app.metrics.base import Metric


class VelocityMetric(Metric):
    name = "velocity"
    description = "Average completed Story Points per iteration."
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

        iterations: dict[str, dict[str, float | int]] = {}

        for item in planning_items:
            iteration = item.iteration
            assert iteration is not None

            iterations.setdefault(
                iteration,
                {"completed": 0.0, "total_items": 0},
            )

            iterations[iteration]["total_items"] += 1

            if item.status == "Done":
                iterations[iteration]["completed"] += item.story_points

        if not iterations:
            return {
                "metric": self.name,
                "value": None,
                "unit": "story_points",
                "sample_size": 0,
                "status": "insufficient_data",
                "message": "No iteration or Story Point data available.",
                "iterations": {},
            }

        completed_values = [
            data["completed"] for data in iterations.values()
        ]
        average_velocity = sum(completed_values) / len(completed_values)

        return {
            "metric": self.name,
            "value": round(average_velocity, 2),
            "unit": "story_points",
            "sample_size": len(iterations),
            "status": "ok",
            "iterations": iterations,
        }

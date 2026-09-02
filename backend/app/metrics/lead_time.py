from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.metrics.base import Metric


class LeadTimeMetric(Metric):
    name = "lead_time"
    description = "Average time from creation to Done."
    category = "flow"
    required_data = "work_items_and_history"

    def calculate(
        self,
        data: tuple[list[WorkItem], list[WorkItemHistory]],
    ) -> dict:
        work_items, histories = data

        histories_by_item: dict[str, list[WorkItemHistory]] = {}

        for event in histories:
            histories_by_item.setdefault(
                event.work_item_id,
                [],
            ).append(event)

        durations = []

        for work_item in work_items:
            item_history = histories_by_item.get(
                work_item.id,
                [],
            )

            completed_at = None

            for event in sorted(
                item_history,
                key=lambda item: item.timestamp,
            ):
                if (
                    event.field == "status"
                    and event.to_value == "Done"
                ):
                    completed_at = event.timestamp
                    break

            if completed_at is None:
                continue

            duration = (
                completed_at - work_item.created_at
            ).total_seconds() / 86400

            durations.append(duration)

        if not durations:
            return {
                "metric": self.name,
                "value": None,
                "unit": "days",
                "sample_size": 0,
            }

        average = sum(durations) / len(durations)

        return {
            "metric": self.name,
            "value": round(average, 2),
            "unit": "days",
            "sample_size": len(durations),
        }
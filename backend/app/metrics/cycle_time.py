from datetime import datetime

from app.core.models.work_item_history import WorkItemHistory
from app.metrics.base import Metric


class CycleTimeMetric(Metric):
    name = "cycle_time"
    description = "Average time from In Progress to Done."
    category = "flow"
    required_data = "history"

    def calculate(
        self,
        histories: list[WorkItemHistory],
    ) -> dict:
        durations = []

        histories_by_item: dict[str, list[WorkItemHistory]] = {}

        for event in histories:
            histories_by_item.setdefault(
                event.work_item_id,
                [],
            ).append(event)

        for item_history in histories_by_item.values():
            started_at = None

            for event in sorted(
                item_history,
                key=lambda item: item.timestamp,
            ):
                if (
                    event.field == "status"
                    and event.to_value == "In Progress"
                ):
                    started_at = event.timestamp

                elif (
                    event.field == "status"
                    and event.to_value == "Done"
                    and started_at is not None
                ):
                    duration = (
                        event.timestamp - started_at
                    ).total_seconds() / 86400

                    durations.append(duration)
                    started_at = None

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
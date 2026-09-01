from app.core.models.work_item_history import WorkItemHistory
from app.metrics.base import Metric


class LeadTimeMetric(Metric):
    name = "lead_time"
    description = "Average time from the first workflow status to Done."
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
            ordered = sorted(
                item_history,
                key=lambda item: item.timestamp,
            )

            started_at = None
            completed_at = None

            for event in ordered:
                if event.field != "status":
                    continue

                if started_at is None:
                    started_at = event.timestamp

                if event.to_value == "Done":
                    completed_at = event.timestamp
                    break

            if started_at is not None and completed_at is not None:
                duration = (
                    completed_at - started_at
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
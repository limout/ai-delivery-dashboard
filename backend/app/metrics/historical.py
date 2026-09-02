from datetime import date, datetime, time, timedelta, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory


class HistoricalMetrics:
    def calculate_wip(
        self,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        history_by_item: dict[str, list[WorkItemHistory]] = {}

        for event in histories:
            history_by_item.setdefault(
                event.work_item_id,
                [],
            ).append(event)

        points = []

        current_date = start_date

        while current_date <= end_date:
            timestamp = datetime.combine(
                current_date,
                time.max,
                tzinfo=timezone.utc,
            )

            wip_count = 0

            for work_item in work_items:
                status = self._status_at(
                    work_item=work_item,
                    history=history_by_item.get(
                        work_item.id,
                        [],
                    ),
                    timestamp=timestamp,
                )

                if status == "In Progress":
                    wip_count += 1

            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": wip_count,
                }
            )

            current_date += timedelta(days=1)

        return {
            "metric": "wip",
            "unit": "items",
            "points": points,
        }

    def _status_at(
        self,
        work_item: WorkItem,
        history: list[WorkItemHistory],
        timestamp: datetime,
    ) -> str | None:
        if work_item.created_at > timestamp:
            return None

        status_events = sorted(
            [
                event
                for event in history
                if event.field == "status"
            ],
            key=lambda item: item.timestamp,
        )

        if not status_events:
            return work_item.status

        first_event = status_events[0]

        status = first_event.from_value

        for event in status_events:
            if event.timestamp > timestamp:
                break

            status = event.to_value

        return status
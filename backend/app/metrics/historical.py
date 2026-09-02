from datetime import date, datetime, time, timedelta, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory


class HistoricalMetrics:
    def calculate(
        self,
        metric: str,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        if metric == "wip":
            points = self.calculate_wip(
                work_items,
                histories,
                start_date,
                end_date,
            )
        elif metric == "throughput":
            points = self.calculate_throughput(
                histories,
                start_date,
                end_date,
            )
        elif metric == "cycle_time":
            points = self.calculate_cycle_time(
                histories,
                start_date,
                end_date,
            )
        elif metric == "lead_time":
            points = self.calculate_lead_time(
                work_items,
                histories,
                start_date,
                end_date,
            )
        else:
            raise ValueError(
                f"Unsupported historical metric: {metric}"
            )

        units = {
            "wip": "items",
            "throughput": "items",
            "cycle_time": "days",
            "lead_time": "days",
        }

        return {
            "metric": metric,
            "unit": units[metric],
            "points": points,
        }

    def calculate_wip(
        self,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        history_by_item = self._group_history(histories)

        points = []

        current_date = start_date

        while current_date <= end_date:
            timestamp = self._end_of_day(current_date)

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

        return points

    def calculate_throughput(
        self,
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        completed_by_date = {}

        for event in histories:
            if (
                event.field == "status"
                and event.to_value == "Done"
            ):
                event_date = event.timestamp.date()

                completed_by_date[event_date] = (
                    completed_by_date.get(event_date, 0) + 1
                )

        return self._build_daily_points(
            completed_by_date,
            start_date,
            end_date,
        )

    def calculate_cycle_time(
        self,
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        history_by_item = self._group_history(histories)

        durations_by_date = {}

        for item_history in history_by_item.values():
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

                    completion_date = event.timestamp.date()

                    durations_by_date.setdefault(
                        completion_date,
                        [],
                    ).append(duration)

                    started_at = None

        points = []

        current_date = start_date

        while current_date <= end_date:
            durations = durations_by_date.get(
                current_date,
                [],
            )

            value = (
                round(sum(durations) / len(durations), 2)
                if durations
                else None
            )

            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": value,
                }
            )

            current_date += timedelta(days=1)

        return points

    def calculate_lead_time(
        self,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        history_by_item = self._group_history(histories)

        durations_by_date = {}

        for work_item in work_items:
            completed_at = None

            for event in sorted(
                history_by_item.get(
                    work_item.id,
                    [],
                ),
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

            completion_date = completed_at.date()

            durations_by_date.setdefault(
                completion_date,
                [],
            ).append(duration)

        points = []

        current_date = start_date

        while current_date <= end_date:
            durations = durations_by_date.get(
                current_date,
                [],
            )

            value = (
                round(sum(durations) / len(durations), 2)
                if durations
                else None
            )

            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": value,
                }
            )

            current_date += timedelta(days=1)

        return points

    def _group_history(
        self,
        histories: list[WorkItemHistory],
    ) -> dict[str, list[WorkItemHistory]]:
        history_by_item = {}

        for event in histories:
            history_by_item.setdefault(
                event.work_item_id,
                [],
            ).append(event)

        return history_by_item

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

        status = status_events[0].from_value

        for event in status_events:
            if event.timestamp > timestamp:
                break

            status = event.to_value

        return status

    def _build_daily_points(
        self,
        values_by_date: dict[date, int],
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        points = []

        current_date = start_date

        while current_date <= end_date:
            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": values_by_date.get(
                        current_date,
                        0,
                    ),
                }
            )

            current_date += timedelta(days=1)

        return points

    def _end_of_day(self, current_date: date) -> datetime:
        return datetime.combine(
            current_date,
            time.max,
            tzinfo=timezone.utc,
        )
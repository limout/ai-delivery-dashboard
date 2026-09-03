from collections import defaultdict
from datetime import date, datetime, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory


class HistoricalMetrics:
    """
    Historical delivery metrics calculated from WorkItems and their history.

    Historical points use a deliberately simple contract:

        {
            "date": "YYYY-MM-DD",
            "value": ...
        }

    No sample_size is included inside individual points.
    """

    STATUS_FIELDS = {
        "status",
        "System.State",
    }

    DONE_STATUSES = {
        "Done",
        "Closed",
        "Resolved",
        "Completed",
    }

    WIP_STATUSES = {
        "New",
        "To Do",
        "Open",
        "In Progress",
        "Review",
        "Testing",
        "Blocked",
    }

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        """
        Normalize naive and timezone-aware datetimes so they can safely
        be compared/subtracted.

        Naive timestamps are treated as UTC.
        """
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @staticmethod
    def _date_range(
        start_date: date,
        end_date: date,
    ) -> list[date]:
        current = start_date
        dates = []

        while current <= end_date:
            dates.append(current)
            current = date.fromordinal(
                current.toordinal() + 1
            )

        return dates

    @classmethod
    def _is_status_event(
        cls,
        event: WorkItemHistory,
    ) -> bool:
        return event.field in cls.STATUS_FIELDS

    @classmethod
    def _events_for_item(
        cls,
        work_item_id: str,
        histories: list[WorkItemHistory],
    ) -> list[WorkItemHistory]:
        events = [
            event
            for event in histories
            if event.work_item_id == work_item_id
        ]

        return sorted(
            events,
            key=lambda event: cls._normalize_datetime(
                event.timestamp
            ),
        )

    @classmethod
    def _status_events_for_item(
        cls,
        work_item_id: str,
        histories: list[WorkItemHistory],
    ) -> list[WorkItemHistory]:
        return [
            event
            for event in cls._events_for_item(
                work_item_id,
                histories,
            )
            if cls._is_status_event(event)
        ]

    @classmethod
    def _status_at_date(
        cls,
        item: WorkItem,
        histories: list[WorkItemHistory],
        current_date: date,
    ) -> str | None:
        """
        Reconstruct the historical status of an item at the end of
        current_date.

        We only trust states that can be reconstructed from recorded
        status transitions.

        Before the first recorded status transition, the historical
        status is unknown and must not be inferred from the current
        WorkItem.status or from the first event's from_value.

        Example:

            2026-08-31:
                To Do -> In Progress

        means:

            2026-08-30 -> unknown
            2026-08-31 -> In Progress
        """

        events = cls._status_events_for_item(
            item.id,
            histories,
        )

        if not events:
            return None

        first_event_date = cls._normalize_datetime(
            events[0].timestamp
        ).date()

        # Before the first recorded transition we do not have enough
        # historical information to reconstruct the status.
        if current_date < first_event_date:
            return None

        status = events[0].from_value

        for event in events:
            event_date = cls._normalize_datetime(
                event.timestamp
            ).date()

            if event_date > current_date:
                break

            status = event.to_value

        return status

    @classmethod
    def _exists_on_date(
        cls,
        item: WorkItem,
        current_date: date,
    ) -> bool:
        """
        Determine whether the item existed on the requested date.

        If created_at is unavailable we cannot establish an earlier
        creation boundary, so we keep the item eligible.
        """

        if item.created_at is None:
            return True

        return item.created_at.date() <= current_date

    @classmethod
    def calculate_wip(
        cls,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Calculate daily Work In Progress.

        An item contributes to WIP when:
        - it existed on that date
        - its reconstructed historical status belongs to WIP_STATUSES
        """

        points = []

        for current_date in cls._date_range(
            start_date,
            end_date,
        ):
            wip_count = 0

            for item in work_items:
                if not cls._exists_on_date(
                    item,
                    current_date,
                ):
                    continue

                status = cls._status_at_date(
                    item,
                    histories,
                    current_date,
                )

                if status in cls.WIP_STATUSES:
                    wip_count += 1

            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": wip_count,
                }
            )

        return {
            "metric": "wip",
            "unit": "items",
            "status": "ok",
            "points": points,
        }

    @classmethod
    def calculate_throughput(
        cls,
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Count completed items by the date of their Done transition.

        Throughput intentionally depends only on history. The current
        WorkItem collection is not required.
        """

        daily_counts: defaultdict[date, int] = defaultdict(int)

        for event in histories:
            if not cls._is_status_event(event):
                continue

            if event.to_value not in cls.DONE_STATUSES:
                continue

            event_date = event.timestamp.date()

            if start_date <= event_date <= end_date:
                daily_counts[event_date] += 1

        points = []

        for current_date in cls._date_range(
            start_date,
            end_date,
        ):
            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": daily_counts.get(
                        current_date,
                        0,
                    ),
                }
            )

        return {
            "metric": "throughput",
            "unit": "items",
            "status": "ok",
            "points": points,
        }

    @classmethod
    def calculate_cycle_time(
        cls,
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Calculate average cycle time per completion day.

        Cycle time is measured from the first transition into
        In Progress to the first transition into a Done state.
        """

        grouped_histories: defaultdict[
            str,
            list[WorkItemHistory],
        ] = defaultdict(list)

        for event in histories:
            grouped_histories[event.work_item_id].append(
                event
            )

        started_at: dict[str, datetime] = {}
        completed_at: dict[str, datetime] = {}

        for work_item_id, events in grouped_histories.items():
            events.sort(
                key=lambda event: cls._normalize_datetime(
                    event.timestamp
                )
            )

            for event in events:
                if not cls._is_status_event(event):
                    continue

                if (
                    event.to_value == "In Progress"
                    and work_item_id not in started_at
                ):
                    started_at[work_item_id] = event.timestamp

                if (
                    event.to_value in cls.DONE_STATUSES
                    and work_item_id not in completed_at
                ):
                    completed_at[work_item_id] = event.timestamp

        daily_values: defaultdict[
            date,
            list[float],
        ] = defaultdict(list)

        for work_item_id, completed_timestamp in completed_at.items():
            started_timestamp = started_at.get(work_item_id)

            if started_timestamp is None:
                continue

            completion_date = completed_timestamp.date()

            if not (
                start_date
                <= completion_date
                <= end_date
            ):
                continue

            started = cls._normalize_datetime(
                started_timestamp
            )
            completed = cls._normalize_datetime(
                completed_timestamp
            )

            cycle_time_days = (
                completed - started
            ).total_seconds() / 86400

            daily_values[completion_date].append(
                cycle_time_days
            )

        points = []

        for current_date in cls._date_range(
            start_date,
            end_date,
        ):
            values = daily_values.get(
                current_date,
                [],
            )

            if values:
                value = round(
                    sum(values) / len(values),
                    2,
                )
            else:
                value = None

            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": value,
                }
            )

        return {
            "metric": "cycle_time",
            "unit": "days",
            "status": "ok",
            "points": points,
        }

    @classmethod
    def calculate_lead_time(
        cls,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Calculate average lead time per completion day.

        Lead time is measured from WorkItem.created_at to the first
        transition into a Done state.
        """

        work_items_by_id = {
            item.id: item
            for item in work_items
        }

        first_done: dict[str, datetime] = {}

        sorted_histories = sorted(
            histories,
            key=lambda event: cls._normalize_datetime(
                event.timestamp
            ),
        )

        for event in sorted_histories:
            if not cls._is_status_event(event):
                continue

            if event.to_value not in cls.DONE_STATUSES:
                continue

            if event.work_item_id not in first_done:
                first_done[event.work_item_id] = (
                    event.timestamp
                )

        daily_values: defaultdict[
            date,
            list[float],
        ] = defaultdict(list)

        for work_item_id, completed_timestamp in first_done.items():
            item = work_items_by_id.get(work_item_id)

            if item is None or item.created_at is None:
                continue

            completion_date = completed_timestamp.date()

            if not (
                start_date
                <= completion_date
                <= end_date
            ):
                continue

            created = cls._normalize_datetime(
                item.created_at
            )
            completed = cls._normalize_datetime(
                completed_timestamp
            )

            lead_time_days = (
                completed - created
            ).total_seconds() / 86400

            daily_values[completion_date].append(
                lead_time_days
            )

        points = []

        for current_date in cls._date_range(
            start_date,
            end_date,
        ):
            values = daily_values.get(
                current_date,
                [],
            )

            if values:
                value = round(
                    sum(values) / len(values),
                    2,
                )
            else:
                value = None

            points.append(
                {
                    "date": current_date.isoformat(),
                    "value": value,
                }
            )

        return {
            "metric": "lead_time",
            "unit": "days",
            "status": "ok",
            "points": points,
        }

    @classmethod
    def calculate(
        cls,
        metric: str,
        work_items: list[WorkItem],
        histories: list[WorkItemHistory],
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Public dispatcher used by the historical metrics API/tests.
        """

        if metric == "wip":
            return cls.calculate_wip(
                work_items=work_items,
                histories=histories,
                start_date=start_date,
                end_date=end_date,
            )

        if metric == "throughput":
            return cls.calculate_throughput(
                histories=histories,
                start_date=start_date,
                end_date=end_date,
            )

        if metric == "cycle_time":
            return cls.calculate_cycle_time(
                histories=histories,
                start_date=start_date,
                end_date=end_date,
            )

        if metric == "lead_time":
            return cls.calculate_lead_time(
                work_items=work_items,
                histories=histories,
                start_date=start_date,
                end_date=end_date,
            )

        raise ValueError(
            f"Unsupported historical metric: {metric}"
        )
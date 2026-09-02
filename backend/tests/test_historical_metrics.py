from datetime import datetime, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.metrics.historical import HistoricalMetrics


def make_work_item(
    item_id: str,
    status: str = "Done",
) -> WorkItem:
    return WorkItem(
        id=item_id,
        source="jira",
        project="KAN",
        type="Task",
        title=f"Test {item_id}",
        status=status,
        priority="Medium",
        assignee=None,
        created_at=datetime(
            2026,
            8,
            30,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        updated_at=datetime(
            2026,
            9,
            2,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        due_date=None,
        iteration=None,
    )


def make_event(
    item_id: str,
    day: int,
    hour: int,
    from_value: str,
    to_value: str,
) -> WorkItemHistory:
    return WorkItemHistory(
        work_item_id=item_id,
        timestamp=datetime(
            2026,
            8 if day <= 31 else 9,
            day if day <= 31 else day - 31,
            hour,
            0,
            tzinfo=timezone.utc,
        ),
        field="status",
        from_value=from_value,
        to_value=to_value,
    )


def test_historical_wip_calculates_daily_values():
    work_items = [
        make_work_item("KAN-1"),
        make_work_item("KAN-2"),
    ]

    histories = [
        make_event(
            "KAN-1",
            30,
            10,
            "To Do",
            "In Progress",
        ),
        WorkItemHistory(
            work_item_id="KAN-1",
            timestamp=datetime(
                2026,
                9,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
        WorkItemHistory(
            work_item_id="KAN-2",
            timestamp=datetime(
                2026,
                8,
                31,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
        ),
    ]

    result = HistoricalMetrics().calculate(
        metric="wip",
        work_items=work_items,
        histories=histories,
        start_date=datetime(
            2026,
            8,
            30,
            tzinfo=timezone.utc,
        ).date(),
        end_date=datetime(
            2026,
            9,
            2,
            tzinfo=timezone.utc,
        ).date(),
    )

    assert result["metric"] == "wip"
    assert result["unit"] == "items"

    assert result["points"] == [
        {"date": "2026-08-30", "value": 1},
        {"date": "2026-08-31", "value": 2},
        {"date": "2026-09-01", "value": 1},
        {"date": "2026-09-02", "value": 1},
    ]


def test_historical_throughput_groups_done_events_by_day():
    histories = [
        make_event(
            "KAN-1",
            30,
            10,
            "In Progress",
            "Done",
        ),
        WorkItemHistory(
            work_item_id="KAN-2",
            timestamp=datetime(
                2026,
                9,
                1,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
        WorkItemHistory(
            work_item_id="KAN-3",
            timestamp=datetime(
                2026,
                9,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
    ]

    result = HistoricalMetrics().calculate(
        metric="throughput",
        work_items=[],
        histories=histories,
        start_date=datetime(
            2026,
            8,
            30,
            tzinfo=timezone.utc,
        ).date(),
        end_date=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ).date(),
    )

    assert result["points"] == [
        {"date": "2026-08-30", "value": 1},
        {"date": "2026-08-31", "value": 0},
        {"date": "2026-09-01", "value": 2},
    ]


def test_historical_cycle_time_groups_average_by_completion_day():
    histories = [
        make_event(
            "KAN-1",
            30,
            10,
            "To Do",
            "In Progress",
        ),
        WorkItemHistory(
            work_item_id="KAN-1",
            timestamp=datetime(
                2026,
                9,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
        WorkItemHistory(
            work_item_id="KAN-2",
            timestamp=datetime(
                2026,
                8,
                31,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
        ),
        WorkItemHistory(
            work_item_id="KAN-2",
            timestamp=datetime(
                2026,
                9,
                1,
                22,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
    ]

    result = HistoricalMetrics().calculate(
        metric="cycle_time",
        work_items=[],
        histories=histories,
        start_date=datetime(
            2026,
            8,
            30,
            tzinfo=timezone.utc,
        ).date(),
        end_date=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ).date(),
    )

    assert result["points"][0] == {
        "date": "2026-08-30",
        "value": None,
    }

    assert result["points"][1] == {
        "date": "2026-08-31",
        "value": None,
    }

    assert result["points"][2] == {
        "date": "2026-09-01",
        "value": 1.75,
    }


def test_historical_lead_time_groups_average_by_completion_day():
    work_items = [
        make_work_item("KAN-1"),
        make_work_item("KAN-2"),
    ]

    histories = [
        WorkItemHistory(
            work_item_id="KAN-1",
            timestamp=datetime(
                2026,
                9,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
        WorkItemHistory(
            work_item_id="KAN-2",
            timestamp=datetime(
                2026,
                9,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
    ]

    result = HistoricalMetrics().calculate(
        metric="lead_time",
        work_items=work_items,
        histories=histories,
        start_date=datetime(
            2026,
            8,
            30,
            tzinfo=timezone.utc,
        ).date(),
        end_date=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ).date(),
    )

    assert result["points"][2]["date"] == "2026-09-01"
    assert result["points"][2]["value"] == 2.08


def test_historical_wip_does_not_count_item_before_creation():
    work_items = [
        make_work_item("KAN-1"),
    ]

    histories = [
        make_event(
            "KAN-1",
            30,
            10,
            "To Do",
            "In Progress",
        ),
    ]

    result = HistoricalMetrics().calculate(
        metric="wip",
        work_items=work_items,
        histories=histories,
        start_date=datetime(
            2026,
            8,
            29,
            tzinfo=timezone.utc,
        ).date(),
        end_date=datetime(
            2026,
            8,
            30,
            tzinfo=timezone.utc,
        ).date(),
    )

    assert result["points"] == [
        {"date": "2026-08-29", "value": 0},
        {"date": "2026-08-30", "value": 1},
    ]


def test_historical_wip_uses_initial_status_from_history():
    work_items = [
        make_work_item("KAN-1"),
    ]

    histories = [
        WorkItemHistory(
            work_item_id="KAN-1",
            timestamp=datetime(
                2026,
                8,
                31,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
        ),
    ]

    result = HistoricalMetrics().calculate(
        metric="wip",
        work_items=work_items,
        histories=histories,
        start_date=datetime(
            2026,
            8,
            30,
            tzinfo=timezone.utc,
        ).date(),
        end_date=datetime(
            2026,
            8,
            31,
            tzinfo=timezone.utc,
        ).date(),
    )

    assert result["points"] == [
        {"date": "2026-08-30", "value": 0},
        {"date": "2026-08-31", "value": 1},
    ]
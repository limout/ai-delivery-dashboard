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


def test_historical_wip_calculates_daily_values():
    work_items = [
        make_work_item("KAN-1"),
        make_work_item("KAN-2"),
    ]

    histories = [
        WorkItemHistory(
            work_item_id="KAN-1",
            timestamp=datetime(
                2026,
                8,
                30,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
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

    historical = HistoricalMetrics()

    result = historical.calculate_wip(
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


def test_historical_wip_does_not_count_item_before_creation():
    work_items = [
        make_work_item("KAN-1"),
    ]

    histories = [
        WorkItemHistory(
            work_item_id="KAN-1",
            timestamp=datetime(
                2026,
                8,
                30,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
        ),
    ]

    historical = HistoricalMetrics()

    result = historical.calculate_wip(
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

    historical = HistoricalMetrics()

    result = historical.calculate_wip(
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
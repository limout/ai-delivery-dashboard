from datetime import datetime, timezone

from app.core.models.work_item_history import WorkItemHistory


def test_create_work_item_history():
    timestamp = datetime(
        2026,
        8,
        20,
        9,
        15,
        tzinfo=timezone.utc,
    )

    event = WorkItemHistory(
        work_item_id="KAN-8",
        timestamp=timestamp,
        field="status",
        from_value="To Do",
        to_value="In Progress",
    )

    assert event.work_item_id == "KAN-8"
    assert event.field == "status"
    assert event.from_value == "To Do"
    assert event.to_value == "In Progress"
    assert event.timestamp == timestamp
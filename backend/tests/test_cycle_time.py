from datetime import datetime, timezone

from app.core.models.work_item_history import WorkItemHistory
from app.metrics.cycle_time import CycleTimeMetric


def test_cycle_time_calculates_average_duration():
    history = [
        WorkItemHistory(
            work_item_id="1",
            timestamp=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
        ),
        WorkItemHistory(
            work_item_id="1",
            timestamp=datetime(
                2026, 8, 23, 9, 0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
    ]

    result = CycleTimeMetric().calculate(history)

    assert result["metric"] == "cycle_time"
    assert result["value"] == 3.0
    assert result["unit"] == "days"
    assert result["sample_size"] == 1
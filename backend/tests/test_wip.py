from datetime import datetime, timezone

from app.core.models.work_item import WorkItem
from app.metrics.wip import WIPMetric


def test_wip_counts_in_progress_items():
    work_items = [
        WorkItem(
            id="1",
            source="fake",
            project="DEMO",
            type="Task",
            title="First",
            status="In Progress",
            created_at=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
        ),
        WorkItem(
            id="2",
            source="fake",
            project="DEMO",
            type="Task",
            title="Second",
            status="Done",
            created_at=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
        ),
        WorkItem(
            id="3",
            source="fake",
            project="DEMO",
            type="Task",
            title="Third",
            status="In Progress",
            created_at=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
        ),
    ]

    result = WIPMetric().calculate(work_items)

    assert result["value"] == 2
    assert result["unit"] == "items"
    assert result["sample_size"] == 3
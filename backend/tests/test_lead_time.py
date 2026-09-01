from datetime import datetime, timezone

from app.core.models.work_item_history import WorkItemHistory
from app.metrics.lead_time import LeadTimeMetric


def test_lead_time_calculates_duration():
    history = [
        WorkItemHistory(
            work_item_id="1",
            timestamp=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value=None,
            to_value="Idea",
        ),
        WorkItemHistory(
            work_item_id="1",
            timestamp=datetime(
                2026, 8, 23, 9, 0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="Idea",
            to_value="Done",
        ),
    ]

    result = LeadTimeMetric().calculate(history)

    assert result["metric"] == "lead_time"
    assert result["value"] == 3.0
    assert result["unit"] == "days"
    assert result["sample_size"] == 1
from app.core.models.work_item import WorkItem
from app.metrics.throughput import ThroughputMetric


def test_throughput_counts_completed_items():
    items = [
        WorkItem(
            id="1",
            source="fake",
            project="DEMO",
            type="Task",
            title="First",
            status="Done",
        ),
        WorkItem(
            id="2",
            source="fake",
            project="DEMO",
            type="Task",
            title="Second",
            status="In Progress",
        ),
        WorkItem(
            id="3",
            source="fake",
            project="DEMO",
            type="Task",
            title="Third",
            status="Done",
        ),
    ]

    result = ThroughputMetric().calculate(items)

    assert result["metric"] == "throughput"
    assert result["value"] == 2
    assert result["unit"] == "items"
    assert result["sample_size"] == 3
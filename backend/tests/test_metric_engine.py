from app.core.models.work_item import WorkItem
from app.metrics.engine import MetricEngine
from app.metrics.registry import get_default_registry


def test_metric_engine_calculates_selected_metrics():
    work_items = [
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

    engine = MetricEngine(get_default_registry())

    result = engine.calculate(
        work_items,
        ["throughput"],
    )

    assert "throughput" in result
    assert result["throughput"]["value"] == 2
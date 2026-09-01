from datetime import datetime, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.metrics.engine import MetricEngine
from app.metrics.registry import MetricRegistry
from app.metrics.throughput import ThroughputMetric
from app.metrics.cycle_time import CycleTimeMetric


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
    ]

    history = [
        WorkItemHistory(
            work_item_id="2",
            timestamp=datetime(
                2026, 8, 20, 9, 0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="To Do",
            to_value="In Progress",
        ),
        WorkItemHistory(
            work_item_id="2",
            timestamp=datetime(
                2026, 8, 23, 9, 0,
                tzinfo=timezone.utc,
            ),
            field="status",
            from_value="In Progress",
            to_value="Done",
        ),
    ]

    registry = MetricRegistry()
    registry.register(ThroughputMetric())
    registry.register(CycleTimeMetric())

    engine = MetricEngine(registry)

    result = engine.calculate(
        work_items=work_items,
        history=history,
        metric_names=[
            "throughput",
            "cycle_time",
        ],
    )

    assert result["throughput"]["value"] == 1
    assert result["cycle_time"]["value"] == 3.0
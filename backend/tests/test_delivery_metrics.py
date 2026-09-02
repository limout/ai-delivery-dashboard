from datetime import datetime, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.metrics.engine import MetricEngine
from app.metrics.registry import MetricRegistry
from app.metrics.throughput import ThroughputMetric
from app.metrics.cycle_time import CycleTimeMetric
from app.metrics.lead_time import LeadTimeMetric
from app.services.delivery_metrics import DeliveryMetricsService


class FakeConnector:
    def get_work_items(self, project):
        return [
            WorkItem(
                id="1",
                source="fake",
                project=project,
                type="Task",
                title="First",
                status="Done",
                created_at=datetime(
                    2026, 8, 20, 9, 0,
                    tzinfo=timezone.utc,
                ),
            ),
            WorkItem(
                id="2",
                source="fake",
                project=project,
                type="Task",
                title="Second",
                status="Done",
                created_at=datetime(
                    2026, 8, 20, 9, 0,
                    tzinfo=timezone.utc,
                ),
            )
        ]

    def get_work_item_history(self, work_item_id):
        if work_item_id == "1":
            return [
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

        return [
            WorkItemHistory(
                work_item_id="2",
                timestamp=datetime(
                    2026, 8, 21, 9, 0,
                    tzinfo=timezone.utc,
                ),
                field="status",
                from_value="To Do",
                to_value="In Progress",
            ),
            WorkItemHistory(
                work_item_id="2",
                timestamp=datetime(
                    2026, 8, 25, 9, 0,
                    tzinfo=timezone.utc,
                ),
                field="status",
                from_value="In Progress",
                to_value="Done",
            ),
        ]


def test_delivery_metrics_service():
    registry = MetricRegistry()

    registry.register(ThroughputMetric())
    registry.register(CycleTimeMetric())
    registry.register(LeadTimeMetric())

    engine = MetricEngine(registry)

    service = DeliveryMetricsService(
        connector=FakeConnector(),
        metric_engine=engine,
    )

    result = service.calculate(
        project="DEMO",
        metric_names=[
            "throughput",
            "cycle_time",
            "lead_time",
        ],
    )

    assert result["throughput"]["value"] == 2
    assert result["cycle_time"]["value"] == 3.5
    assert result["lead_time"]["value"] == 4.0
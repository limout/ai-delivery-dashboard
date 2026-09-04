from app.core.models.delivery_semantics import DeliveryRole
from app.core.models.work_item import WorkItem
from app.metrics.engine import MetricEngine
from app.metrics.registry import get_default_registry
from app.services.insight_service import InsightService


class FakeConnector:
    def get_work_items(self, project):
        return [
            WorkItem(
                id="1",
                source="test",
                project=project,
                type="Task",
                title="Task 1",
                status="In Progress",
                delivery_role=DeliveryRole.EXECUTION_ITEM,
            )
        ]

    def get_work_item_history(self, work_item_id):
        return []


def test_insight_service_returns_expected_structure():
    connector = FakeConnector()
    engine = MetricEngine(get_default_registry())
    service = InsightService(connector, engine)

    result = service.analyze(
        project="TEST",
        metric_names=["wip", "throughput"],
        historical_metric_names=[],
    )

    assert result["project"] == "TEST"
    assert "metrics" in result
    assert "historical" in result
    assert "insights" in result
    assert isinstance(result["insights"], list)

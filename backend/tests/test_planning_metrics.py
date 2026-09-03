from app.core.models.delivery_semantics import DeliveryRole
from app.core.models.work_item import WorkItem
from app.metrics.commitment_vs_completed import CommitmentVsCompletedMetric
from app.metrics.velocity import VelocityMetric


def make_item(
    item_id: str,
    iteration: str,
    story_points: float,
    status: str,
) -> WorkItem:
    return WorkItem(
        id=item_id,
        source="azure_devops",
        project="KAN",
        type="User Story",
        title=f"Story {item_id}",
        status=status,
        iteration=iteration,
        story_points=story_points,
        delivery_role=DeliveryRole.PLANNING_ITEM,
    )


def make_feature_without_points() -> WorkItem:
    return WorkItem(
        id="feature-1",
        source="azure_devops",
        project="KAN",
        type="Feature",
        title="Feature",
        status="Done",
        iteration="KAN\\Sprint 4",
    )


def test_velocity_uses_completed_story_points_per_iteration():
    items = [
        make_item("1", "KAN\\Sprint 1", 8, "Done"),
        make_item("2", "KAN\\Sprint 1", 5, "Done"),
        make_item("3", "KAN\\Sprint 1", 8, "In Progress"),
        make_item("4", "KAN\\Sprint 1", 5, "New"),
        make_item("5", "KAN\\Sprint 2", 8, "Done"),
        make_item("6", "KAN\\Sprint 2", 5, "Done"),
        make_item("7", "KAN\\Sprint 2", 8, "Done"),
        make_item("8", "KAN\\Sprint 3", 8, "Done"),
        make_item("9", "KAN\\Sprint 3", 8, "In Progress"),
        make_item("10", "KAN\\Sprint 3", 8, "New"),
    ]

    result = VelocityMetric().calculate(items)

    assert result["value"] == 14.0
    assert result["sample_size"] == 3
    assert result["iterations"]["KAN\\Sprint 1"]["completed"] == 13
    assert result["iterations"]["KAN\\Sprint 2"]["completed"] == 21
    assert result["iterations"]["KAN\\Sprint 3"]["completed"] == 8


def test_commitment_vs_completed_is_calculated_per_iteration():
    items = [
        make_item("1", "KAN\\Sprint 1", 8, "Done"),
        make_item("2", "KAN\\Sprint 1", 5, "Done"),
        make_item("3", "KAN\\Sprint 1", 8, "In Progress"),
        make_item("4", "KAN\\Sprint 1", 5, "New"),
        make_item("5", "KAN\\Sprint 2", 8, "Done"),
        make_item("6", "KAN\\Sprint 2", 5, "Done"),
        make_item("7", "KAN\\Sprint 2", 8, "Done"),
        make_item("8", "KAN\\Sprint 3", 8, "Done"),
        make_item("9", "KAN\\Sprint 3", 8, "In Progress"),
        make_item("10", "KAN\\Sprint 3", 8, "New"),
    ]

    result = CommitmentVsCompletedMetric().calculate(items)

    assert result["value"] == 61.11
    assert result["sample_size"] == 3
    assert result["iterations"]["KAN\\Sprint 1"]["completion_percentage"] == 50.0
    assert result["iterations"]["KAN\\Sprint 2"]["completion_percentage"] == 100.0
    assert result["iterations"]["KAN\\Sprint 3"]["completion_percentage"] == 33.33


def test_planning_metrics_ignore_items_without_story_points():
    items = [
        make_feature_without_points(),
        make_item("1", "KAN\\Sprint 1", 8, "Done"),
    ]

    velocity = VelocityMetric().calculate(items)
    commitment = CommitmentVsCompletedMetric().calculate(items)

    assert velocity["value"] == 8.0
    assert commitment["value"] == 100.0

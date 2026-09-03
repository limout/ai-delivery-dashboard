from datetime import datetime

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
        source="azure",
        project="TestProject",
        type="User Story",
        title=f"Story {item_id}",
        status=status,
        story_points=story_points,
        iteration=iteration,
        delivery_role=DeliveryRole.PLANNING_ITEM,
        created_at=datetime(2026, 1, 1),
    )


def test_velocity_calculates_average_completed_story_points():
    items = [
        make_item("1", "Sprint 1", 8, "Done"),
        make_item("2", "Sprint 1", 5, "Done"),
        make_item("3", "Sprint 1", 3, "In Progress"),
        make_item("4", "Sprint 2", 8, "Done"),
        make_item("5", "Sprint 2", 5, "Done"),
    ]

    result = VelocityMetric().calculate(items)

    assert result["metric"] == "velocity"
    assert result["value"] == 13.0
    assert result["unit"] == "story_points"
    assert result["sample_size"] == 2

    assert result["iterations"]["Sprint 1"]["completed"] == 13
    assert result["iterations"]["Sprint 2"]["completed"] == 13


def test_velocity_ignores_execution_items():
    items = [
        make_item("1", "Sprint 1", 8, "Done"),
    ]

    items.append(
        WorkItem(
            id="2",
            source="azure",
            project="TestProject",
            type="Task",
            title="Execution task",
            status="Done",
            story_points=100,
            iteration="Sprint 1",
            delivery_role=DeliveryRole.EXECUTION_ITEM,
        )
    )

    result = VelocityMetric().calculate(items)

    assert result["value"] == 8.0


def test_velocity_returns_insufficient_data_without_iterations():
    items = [
        WorkItem(
            id="1",
            source="azure",
            project="TestProject",
            type="User Story",
            title="Story",
            status="Done",
            story_points=8,
            delivery_role=DeliveryRole.PLANNING_ITEM,
        )
    ]

    result = VelocityMetric().calculate(items)

    assert result["value"] is None
    assert result["status"] == "insufficient_data"


def test_commitment_vs_completed():
    items = [
        make_item("1", "Sprint 1", 8, "Done"),
        make_item("2", "Sprint 1", 5, "Done"),
        make_item("3", "Sprint 1", 3, "In Progress"),
        make_item("4", "Sprint 2", 8, "Done"),
        make_item("5", "Sprint 2", 8, "In Progress"),
    ]

    result = CommitmentVsCompletedMetric().calculate(items)

    assert result["metric"] == "commitment_vs_completed"
    assert result["value"] == 65.62
    assert result["unit"] == "percent"
    assert result["sample_size"] == 2

    assert result["iterations"]["Sprint 1"]["committed"] == 16
    assert result["iterations"]["Sprint 1"]["completed"] == 13
    assert result["iterations"]["Sprint 1"]["completion_percentage"] == 81.25

    assert result["iterations"]["Sprint 2"]["committed"] == 16
    assert result["iterations"]["Sprint 2"]["completed"] == 8
    assert result["iterations"]["Sprint 2"]["completion_percentage"] == 50.0


def test_commitment_vs_completed_returns_insufficient_data_without_story_points():
    items = [
        WorkItem(
            id="1",
            source="jira",
            project="TestProject",
            type="Story",
            title="Story",
            status="Done",
            iteration="Sprint 1",
            story_points=None,
            delivery_role=DeliveryRole.PLANNING_ITEM,
        )
    ]

    result = CommitmentVsCompletedMetric().calculate(items)

    assert result["value"] is None
    assert result["status"] == "insufficient_data"
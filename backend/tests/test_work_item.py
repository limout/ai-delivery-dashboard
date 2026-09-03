from app.core.models.work_item import WorkItem


def test_create_work_item():
    item = WorkItem(
        id="KAN-8",
        source="jira",
        project="KAN",
        type="Task",
        title="Prepare release v1.0",
        status="In Progress",
        priority="High",
        assignee="Eugene",
        parent_id="KAN-1",
        story_points=5,
    )

    assert item.id == "KAN-8"
    assert item.source == "jira"
    assert item.status == "In Progress"
    assert item.priority == "High"
    assert item.parent_id == "KAN-1"
    assert item.story_points == 5

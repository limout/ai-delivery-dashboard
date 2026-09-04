from datetime import datetime, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.services.evidence import EvidenceService


def item(item_id="KAN-1", status="In Progress"):
    return WorkItem(
        id=item_id,
        source="jira",
        project="KAN",
        type="Task",
        title=f"Task {item_id}",
        status=status,
        assignee="Eugene",
    )


def event(item_id, day, from_value, to_value):
    return WorkItemHistory(
        work_item_id=item_id,
        timestamp=datetime(2026, 9, day, 10, tzinfo=timezone.utc),
        field="status",
        from_value=from_value,
        to_value=to_value,
    )


def test_build_adds_wip_and_blocked_evidence():
    result = EvidenceService().build(
        [{"id": "wip-congestion", "severity": "high"}],
        [item("KAN-1", "In Progress"), item("KAN-2", "Blocked")],
        [
            event("KAN-1", 1, "To Do", "In Progress"),
            event("KAN-2", 2, "In Progress", "Blocked"),
        ],
        now=datetime(2026, 9, 4, 10, tzinfo=timezone.utc),
    )

    evidence = result[0]["evidence"]
    assert evidence["wip_count"] == 2
    assert evidence["blocked_count"] == 1
    assert evidence["wip_items"][0]["id"] == "KAN-1"
    assert evidence["blocked_items"][0]["id"] == "KAN-2"
    assert evidence["wip_items"][0]["age_days"] == 3.0


def test_completed_item_is_not_wip_evidence():
    result = EvidenceService().build(
        [{"id": "x"}],
        [item("KAN-1", "Done")],
        [event("KAN-1", 1, "In Progress", "Done")],
        now=datetime(2026, 9, 4, 10, tzinfo=timezone.utc),
    )

    assert result[0]["evidence"]["wip_count"] == 0
    assert result[0]["evidence"]["blocked_count"] == 0

from unittest.mock import Mock

from app.connectors.jira.connector import JiraConnector


def test_jira_connector_reads_work_items():
    connector = JiraConnector()

    items = connector.get_work_items("KAN")

    assert len(items) > 0

    item = items[0]

    assert item.source == "jira"
    assert item.project == "KAN"
    assert item.id.startswith("KAN-")
    assert item.title
    assert item.delivery_role is not None

def test_jira_work_item_normalizes_parent_and_story_points(monkeypatch):
    connector = JiraConnector.__new__(JiraConnector)
    monkeypatch.setattr(
        "app.connectors.jira.connector.settings.jira_story_points_field",
        "customfield_10016",
        raising=False,
    )

    issue = {
        "key": "KAN-10",
        "fields": {
            "summary": "Historical metrics",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "Eugene"},
            "issuetype": {"name": "Story"},
            "created": "2026-09-01T10:00:00Z",
            "updated": "2026-09-02T10:00:00Z",
            "duedate": None,
            "parent": {"key": "KAN-1"},
            "customfield_10016": 5,
        },
    }

    item = connector._to_work_item(issue, "KAN")

    assert item.parent_id == "KAN-1"
    assert item.story_points == 5
    assert item.type == "Story"

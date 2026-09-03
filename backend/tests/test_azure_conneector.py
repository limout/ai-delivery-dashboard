from unittest.mock import Mock

import pytest

from app.connectors.azure.connector import AzureDevOpsConnector
from app.core.config import settings


@pytest.fixture
def connector(monkeypatch):
    monkeypatch.setattr(settings, "azure_devops_org", "outlim")
    monkeypatch.setattr(settings, "azure_devops_pat", "test-pat")
    monkeypatch.setattr(settings, "azure_devops_team", "KAN Team")
    return AzureDevOpsConnector()


def test_connector_requires_organization(monkeypatch):
    monkeypatch.setattr(settings, "azure_devops_org", "")
    monkeypatch.setattr(settings, "azure_devops_pat", "test-pat")

    with pytest.raises(ValueError, match="AZURE_DEVOPS_ORG is missing"):
        AzureDevOpsConnector()


def test_connector_requires_pat(monkeypatch):
    monkeypatch.setattr(settings, "azure_devops_org", "outlim")
    monkeypatch.setattr(settings, "azure_devops_pat", "")

    with pytest.raises(ValueError, match="AZURE_DEVOPS_PAT is missing"):
        AzureDevOpsConnector()


def test_get_projects(connector):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "value": [{"id": "project-1", "name": "KAN"}]
    }

    connector.session.get = Mock(return_value=response)

    assert connector.get_projects() == [{
        "id": "project-1",
        "key": "KAN",
        "name": "KAN",
    }]


def test_get_work_items_normalizes_fields(connector):
    wiql_response = Mock()
    wiql_response.raise_for_status.return_value = None
    wiql_response.json.return_value = {
        "workItems": [{"id": 101}, {"id": 102}]
    }

    details_response = Mock()
    details_response.raise_for_status.return_value = None
    details_response.json.return_value = {
        "value": [
            {
                "id": 101,
                "fields": {
                    "System.WorkItemType": "Task",
                    "System.Title": "Build dashboard API",
                    "System.State": "Active",
                    "Microsoft.VSTS.Common.Priority": 2,
                    "System.AssignedTo": {"displayName": "Eugene"},
                    "System.CreatedDate": "2026-09-01T10:00:00Z",
                    "System.ChangedDate": "2026-09-02T12:00:00Z",
                    "Microsoft.VSTS.Scheduling.DueDate": "2026-09-05T00:00:00Z",
                    "Microsoft.VSTS.Scheduling.StoryPoints": None,
                    "System.IterationPath": "KAN\\Sprint 1",
                },
                "relations": [
                    {
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": "https://dev.azure.com/outlim/KAN/_apis/wit/workItems/100",
                    }
                ],
            },
            {
                "id": 102,
                "fields": {
                    "System.WorkItemType": "Bug",
                    "System.Title": "Fix filters",
                    "System.State": "Closed",
                    "Microsoft.VSTS.Scheduling.StoryPoints": 3,
                },
                "relations": [],
            },
        ]
    }

    connector.session.post = Mock(return_value=wiql_response)
    connector.session.get = Mock(return_value=details_response)

    items = connector.get_work_items("KAN")

    assert len(items) == 2
    assert items[0].id == "101"
    assert items[0].source == "azure_devops"
    assert items[0].status == "In Progress"
    assert items[0].priority == "2"
    assert items[0].assignee == "Eugene"
    assert items[0].iteration == "KAN\\Sprint 1"
    assert items[0].parent_id == "100"
    assert items[0].story_points is None

    assert items[1].id == "102"
    assert items[1].status == "Done"
    assert items[1].parent_id is None
    assert items[1].story_points == 3


def test_get_work_item_history_normalizes_state_and_identity(connector):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "value": [
            {
                "id": 1,
                "revisedDate": "2026-09-01T10:00:00Z",
                "fields": {
                    "System.State": {
                        "oldValue": "New",
                        "newValue": "Active",
                    },
                    "System.AssignedTo": {
                        "oldValue": None,
                        "newValue": {"displayName": "Eugene"},
                    },
                },
            },
            {
                "id": 2,
                "revisedDate": "2026-09-02T12:00:00Z",
                "fields": {
                    "System.State": {
                        "oldValue": "Active",
                        "newValue": "Closed",
                    }
                },
            },
        ]
    }

    connector.session.get = Mock(return_value=response)

    history = connector.get_work_item_history("101")

    assert len(history) == 3
    assert history[0].field == "System.State"
    assert history[0].from_value == "New"
    assert history[0].to_value == "In Progress"
    assert history[1].field == "System.AssignedTo"
    assert history[1].to_value == "Eugene"
    assert history[2].from_value == "In Progress"
    assert history[2].to_value == "Done"


def test_get_iterations_returns_normalized_iterations(connector):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "value": [{
            "id": "iteration-1",
            "name": "Sprint 1",
            "path": "KAN\\Sprint 1",
            "attributes": {
                "startDate": "2026-09-01T00:00:00Z",
                "finishDate": "2026-09-14T00:00:00Z",
                "timeFrame": "current",
            },
        }]
    }

    connector.session.get = Mock(return_value=response)

    assert connector.get_iterations("KAN") == [{
        "id": "iteration-1",
        "name": "Sprint 1",
        "path": "KAN\\Sprint 1",
        "start_date": "2026-09-01T00:00:00Z",
        "finish_date": "2026-09-14T00:00:00Z",
        "time_frame": "current",
    }]


def test_get_iterations_returns_empty_without_team(monkeypatch):
    monkeypatch.setattr(settings, "azure_devops_org", "outlim")
    monkeypatch.setattr(settings, "azure_devops_pat", "test-pat")
    monkeypatch.setattr(settings, "azure_devops_team", "")

    connector = AzureDevOpsConnector()
    connector.session.get = Mock()

    assert connector.get_iterations("KAN") == []
    connector.session.get.assert_not_called()


def test_get_releases_returns_empty(connector):
    assert connector.get_releases("KAN") == []

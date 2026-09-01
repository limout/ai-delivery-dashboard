from datetime import datetime

from app.connectors.jira.connector import JiraConnector
from app.core.models.work_item_history import WorkItemHistory


def test_jira_history_is_normalized(monkeypatch):
    connector = JiraConnector()

    jira_response = {
        "changelog": {
            "histories": [
                {
                    "created": "2026-08-20T09:15:00.000+0000",
                    "items": [
                        {
                            "field": "status",
                            "fromString": "To Do",
                            "toString": "In Progress",
                        }
                    ],
                },
                {
                    "created": "2026-08-23T16:40:00.000+0000",
                    "items": [
                        {
                            "field": "status",
                            "fromString": "In Progress",
                            "toString": "Done",
                        }
                    ],
                },
            ]
        }
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return jira_response

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        connector.session,
        "get",
        fake_get,
    )

    history = connector.get_work_item_history("KAN-8")

    assert len(history) == 2

    assert isinstance(history[0], WorkItemHistory)

    assert history[0].work_item_id == "KAN-8"
    assert history[0].field == "status"
    assert history[0].from_value == "To Do"
    assert history[0].to_value == "In Progress"

    assert history[1].from_value == "In Progress"
    assert history[1].to_value == "Done"

    assert isinstance(
        history[0].timestamp,
        datetime,
    )
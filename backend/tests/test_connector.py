from app.core.connectors.base import DeliveryConnector
from app.core.models.work_item import WorkItem


class FakeConnector(DeliveryConnector):

    def get_projects(self):
        return [
            {
                "id": "demo",
                "name": "Demo Project",
            }
        ]

    def get_work_items(self, project):
        return [
            WorkItem(
                id="DEMO-1",
                source="fake",
                project=project,
                type="Task",
                title="Implement payment API",
                status="In Progress",
                priority="High",
            )
        ]

    def get_work_item_history(self, work_item_id):
        return []

    def get_iterations(self, project):
        return []

    def get_releases(self, project):
        return []


def test_fake_connector_returns_work_items():
    connector = FakeConnector()

    projects = connector.get_projects()
    items = connector.get_work_items("demo")

    assert projects[0]["name"] == "Demo Project"
    assert len(items) == 1
    assert items[0].id == "DEMO-1"
    assert items[0].source == "fake"
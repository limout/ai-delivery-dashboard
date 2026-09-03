import requests

from app.core.config import settings
from app.core.connectors.base import DeliveryConnector
from app.core.models.delivery_semantics import get_delivery_role
from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory


class JiraConnector(DeliveryConnector):

    def __init__(self):
        if not settings.jira_url:
            raise ValueError("JIRA_URL is missing")

        if not settings.jira_email:
            raise ValueError("JIRA_EMAIL is missing")

        if not settings.jira_api_token:
            raise ValueError("JIRA_API_TOKEN is missing")

        self.base_url = settings.jira_url.rstrip("/")

        self.session = requests.Session()
        self.session.auth = (
            settings.jira_email,
            settings.jira_api_token,
        )
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def get_projects(self) -> list[dict]:
        response = self.session.get(
            f"{self.base_url}/rest/api/3/project/search",
            params={"maxResults": 50},
        )
        response.raise_for_status()

        return [
            {
                "id": project["id"],
                "key": project["key"],
                "name": project["name"],
            }
            for project in response.json().get("values", [])
        ]

    def get_work_items(self, project: str) -> list[WorkItem]:
        fields = (
            "summary,status,priority,assignee,"
            "created,updated,duedate,issuetype,parent"
        )

        story_points_field = getattr(
            settings,
            "jira_story_points_field",
            "customfield_10016",
        )

        if story_points_field not in fields.split(","):
            fields = f"{fields},{story_points_field}"

        response = self.session.get(
            f"{self.base_url}/rest/api/3/search/jql",
            params={
                "jql": f"project = {project} ORDER BY created ASC",
                "maxResults": 50,
                "fields": fields,
            },
        )
        response.raise_for_status()

        return [
            self._to_work_item(issue, project)
            for issue in response.json().get("issues", [])
        ]

    def get_work_item_history(
        self,
        work_item_id: str,
    ) -> list[WorkItemHistory]:
        response = self.session.get(
            f"{self.base_url}/rest/api/3/issue/{work_item_id}",
            params={"expand": "changelog"},
        )
        response.raise_for_status()

        histories = response.json().get(
            "changelog",
            {},
        ).get("histories", [])

        result = []

        for history in histories:
            timestamp = history.get("created")

            for item in history.get("items", []):
                result.append(
                    WorkItemHistory(
                        work_item_id=work_item_id,
                        timestamp=timestamp,
                        field=item.get("field", ""),
                        from_value=item.get("fromString"),
                        to_value=item.get("toString"),
                    )
                )

        return result

    def get_iterations(self, project: str) -> list[dict]:
        # Jira Scrum iteration support will be added through
        # the Agile API when we implement Scrum metrics.
        return []

    def get_releases(self, project: str) -> list[dict]:
        response = self.session.get(
            f"{self.base_url}/rest/api/3/project/{project}/versions",
        )
        response.raise_for_status()

        return [
            {
                "id": version["id"],
                "name": version["name"],
                "released": version.get("released", False),
                "release_date": version.get("releaseDate"),
            }
            for version in response.json()
        ]

    def _to_work_item(
        self,
        issue: dict,
        project: str,
    ) -> WorkItem:
        fields = issue["fields"]

        priority = fields.get("priority")
        assignee = fields.get("assignee")
        issue_type = fields.get("issuetype")
        parent = fields.get("parent")

        story_points_field = getattr(
            settings,
            "jira_story_points_field",
            "customfield_10016",
        )

        work_item_type = (
            issue_type["name"]
            if issue_type
            else "Unknown"
        )

        return WorkItem(
            id=issue["key"],
            source="jira",
            project=project,
            type=work_item_type,
            title=fields.get("summary", ""),
            status=(
                fields.get("status", {}).get("name")
                if fields.get("status")
                else None
            ),
            priority=(
                priority["name"]
                if priority
                else None
            ),
            assignee=(
                assignee.get("displayName")
                if assignee
                else None
            ),
            created_at=fields.get("created"),
            updated_at=fields.get("updated"),
            due_date=fields.get("duedate"),
            parent_id=parent.get("key") if parent else None,
            story_points=_to_story_points(
                fields.get(story_points_field)
            ),
            delivery_role=get_delivery_role(
                source="jira",
                work_item_type=work_item_type,
            ),
        )


def _to_story_points(value) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
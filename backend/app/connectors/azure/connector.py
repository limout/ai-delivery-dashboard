import base64
import re

import requests

from app.core.config import settings
from app.core.connectors.base import DeliveryConnector
from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.core.models.delivery_semantics import DeliveryRole


class AzureDevOpsConnector(DeliveryConnector):
    """Azure DevOps connector that normalizes Boards data into our core models."""

    API_VERSION = "7.1"

    STATUS_MAP = {
        "New": "New",
        "Active": "In Progress",
        "Resolved": "Done",
        "Closed": "Done",
    }

    PARENT_RELATION = "System.LinkTypes.Hierarchy-Reverse"

    ROLE_MAP = {
        "Feature": DeliveryRole.PLANNING_ITEM,
        "User Story": DeliveryRole.PLANNING_ITEM,
        "Task": DeliveryRole.EXECUTION_ITEM,
        "Bug": DeliveryRole.DEFECT,
    }

    def __init__(self):
        if not settings.azure_devops_org:
            raise ValueError("AZURE_DEVOPS_ORG is missing")

        if not settings.azure_devops_pat:
            raise ValueError("AZURE_DEVOPS_PAT is missing")

        self.organization = settings.azure_devops_org
        self.base_url = f"https://dev.azure.com/{self.organization}"

        self.session = requests.Session()

        token = base64.b64encode(
            f":{settings.azure_devops_pat}".encode("utf-8")
        ).decode("ascii")

        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {token}",
        })

    def get_projects(self) -> list[dict]:
        response = self.session.get(
            f"{self.base_url}/_apis/projects",
            params={
                "api-version": self.API_VERSION,
                "$top": 100,
            },
        )
        response.raise_for_status()

        return [
            {
                "id": project["id"],
                "key": project["name"],
                "name": project["name"],
            }
            for project in response.json().get("value", [])
        ]

    def get_work_items(self, project: str) -> list[WorkItem]:
        wiql = {
            "query": (
                "SELECT [System.Id] "
                "FROM WorkItems "
                f"WHERE [System.TeamProject] = '{project}' "
                "ORDER BY [System.CreatedDate] ASC"
            )
        }

        response = self.session.post(
            f"{self.base_url}/{project}/_apis/wit/wiql",
            params={"api-version": self.API_VERSION},
            json=wiql,
        )
        response.raise_for_status()

        ids = [
            item["id"]
            for item in response.json().get("workItems", [])
        ]

        if not ids:
            return []

        result: list[WorkItem] = []

        for start in range(0, len(ids), 200):
            batch_ids = ids[start:start + 200]

            details_response = self.session.get(
                f"{self.base_url}/_apis/wit/workitems",
                params={
                    "ids": ",".join(str(item_id) for item_id in batch_ids),
                    "$expand": "relations",
                    "api-version": self.API_VERSION,
                },
            )
            details_response.raise_for_status()

            result.extend(
                self._to_work_item(item, project)
                for item in details_response.json().get("value", [])
            )

        return result

    def get_work_item_history(
        self,
        work_item_id: str,
    ) -> list[WorkItemHistory]:
        response = self.session.get(
            f"{self.base_url}/_apis/wit/workItems/{work_item_id}/updates",
            params={"api-version": self.API_VERSION},
        )
        response.raise_for_status()

        result: list[WorkItemHistory] = []

        for update in response.json().get("value", []):
            timestamp = update.get("revisedDate")

            for field, change in update.get("fields", {}).items():
                if not isinstance(change, dict):
                    continue

                old_value = change.get("oldValue")
                new_value = change.get("newValue")

                if field == "System.State":
                    old_value = self._normalize_status(old_value)
                    new_value = self._normalize_status(new_value)
                elif field == "System.AssignedTo":
                    old_value = self._identity_name(old_value)
                    new_value = self._identity_name(new_value)

                result.append(
                    WorkItemHistory(
                        work_item_id=str(work_item_id),
                        timestamp=timestamp,
                        field=field,
                        from_value=self._stringify(old_value),
                        to_value=self._stringify(new_value),
                    )
                )

        return result

    def get_iterations(self, project: str) -> list[dict]:
        if not settings.azure_devops_team:
            return []

        response = self.session.get(
            f"{self.base_url}/{project}/{settings.azure_devops_team}"
            "/_apis/work/teamsettings/iterations",
            params={"api-version": self.API_VERSION},
        )
        response.raise_for_status()

        return [
            {
                "id": iteration["id"],
                "name": iteration["name"],
                "path": iteration.get("path"),
                "start_date": iteration.get("attributes", {}).get("startDate"),
                "finish_date": iteration.get("attributes", {}).get("finishDate"),
                "time_frame": iteration.get("attributes", {}).get("timeFrame"),
            }
            for iteration in response.json().get("value", [])
        ]

    def get_releases(self, project: str) -> list[dict]:
        # Azure Boards does not have a Jira-style project versions endpoint.
        return []

    def _to_work_item(self, item: dict, project: str) -> WorkItem:
        fields = item.get("fields", {})

        return WorkItem(
            id=str(item["id"]),
            source="azure_devops",
            project=project,
            type=fields.get("System.WorkItemType", "Unknown"),
            title=fields.get("System.Title", ""),
            status=self._normalize_status(fields.get("System.State")),
            priority=self._stringify(
                fields.get("Microsoft.VSTS.Common.Priority")
            ),
            assignee=self._identity_name(
                fields.get("System.AssignedTo")
            ),
            created_at=fields.get("System.CreatedDate"),
            updated_at=fields.get("System.ChangedDate"),
            due_date=fields.get("Microsoft.VSTS.Scheduling.DueDate"),
            iteration=fields.get("System.IterationPath"),
            parent_id=self._get_parent_id(item),
            story_points=self._to_story_points(
                fields.get("Microsoft.VSTS.Scheduling.StoryPoints")
            ),
            delivery_role=self.ROLE_MAP.get(
                fields.get("System.WorkItemType", "Unknown"),
                DeliveryRole.UNKNOWN,
            ),
        )

    @classmethod
    def _normalize_status(cls, value) -> str | None:
        if value is None:
            return None
        return cls.STATUS_MAP.get(str(value), str(value))

    @classmethod
    def _get_parent_id(cls, item: dict) -> str | None:
        for relation in item.get("relations", []):
            if relation.get("rel") != cls.PARENT_RELATION:
                continue

            url = relation.get("url", "")
            match = re.search(r"/workItems/(\d+)$", url)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _to_story_points(value) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _identity_name(value) -> str | None:
        if value is None:
            return None

        if isinstance(value, dict):
            return (
                value.get("displayName")
                or value.get("uniqueName")
                or value.get("id")
            )

        return str(value)

    @staticmethod
    def _stringify(value) -> str | None:
        if value is None:
            return None

        if isinstance(value, dict):
            return AzureDevOpsConnector._identity_name(value)

        return str(value)

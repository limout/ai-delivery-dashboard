from __future__ import annotations

import base64
import time

import requests

from app.core.config import settings


API_VERSION = "7.1"
SEED_PREFIX = "[AI Dashboard Seed]"

STORY_DEFINITIONS = [
    # Sprint 1: 26 committed / 13 completed
    {
        "sprint": "Sprint 1",
        "title": "Azure DevOps connector",
        "story_points": 8,
        "final_state": "Closed",
        "tasks": ["Implement connector", "Add authentication", "Add connector tests"],
    },
    {
        "sprint": "Sprint 1",
        "title": "Historical delivery metrics",
        "story_points": 5,
        "final_state": "Closed",
        "tasks": ["Historical API", "Metric calculations", "Dashboard charts"],
    },
    {
        "sprint": "Sprint 1",
        "title": "Insight Engine",
        "story_points": 8,
        "final_state": "Active",
        "tasks": ["Define delivery signals", "Risk detection"],
    },
    {
        "sprint": "Sprint 1",
        "title": "AI recommendations",
        "story_points": 5,
        "final_state": "New",
        "tasks": ["Ollama integration", "Recommendation prompt"],
    },

    # Sprint 2: 21 committed / 21 completed
    {
        "sprint": "Sprint 2",
        "title": "Azure DevOps connector hardening",
        "story_points": 8,
        "final_state": "Closed",
        "tasks": ["Retry handling", "Error mapping"],
    },
    {
        "sprint": "Sprint 2",
        "title": "Historical trend charts",
        "story_points": 5,
        "final_state": "Closed",
        "tasks": ["Chart API", "Trend rendering"],
    },
    {
        "sprint": "Sprint 2",
        "title": "Data quality signals",
        "story_points": 8,
        "final_state": "Closed",
        "tasks": ["Missing data checks", "Quality summary"],
    },

    # Sprint 3: 24 committed / 8 completed
    {
        "sprint": "Sprint 3",
        "title": "Insight Engine v2",
        "story_points": 8,
        "final_state": "Closed",
        "tasks": ["Risk rules", "Signal aggregation"],
    },
    {
        "sprint": "Sprint 3",
        "title": "Planning metrics",
        "story_points": 8,
        "final_state": "Active",
        "tasks": ["Velocity", "Commitment tracking"],
    },
    {
        "sprint": "Sprint 3",
        "title": "AI recommendations v2",
        "story_points": 8,
        "final_state": "New",
        "tasks": ["Recommendation context", "AI response contract"],
    },
]


class AzureSeedClient:
    def __init__(self):
        self.organization = settings.azure_devops_org
        self.project = settings.azure_devops_project
        self.team = settings.azure_devops_team

        if not self.organization:
            raise ValueError("AZURE_DEVOPS_ORG is missing")
        if not settings.azure_devops_pat:
            raise ValueError("AZURE_DEVOPS_PAT is missing")
        if not self.project:
            raise ValueError("AZURE_DEVOPS_PROJECT is missing")
        if not self.team:
            raise ValueError("AZURE_DEVOPS_TEAM is missing")

        self.base_url = f"https://dev.azure.com/{self.organization}"

        token = base64.b64encode(
            f":{settings.azure_devops_pat}".encode("utf-8")
        ).decode("ascii")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Basic {token}",
            }
        )

    def _raise_with_details(self, response: requests.Response) -> None:
        if response.ok:
            return

        print()
        print("Azure DevOps API error:")
        print("Status:", response.status_code)
        print("URL:", response.url)
        print("Response:", response.text)
        print()

        response.raise_for_status()

    def get_existing_seed_items(self) -> list[dict]:
        url = f"{self.base_url}/{self.project}/_apis/wit/wiql"

        wiql = {
            "query": (
                "SELECT [System.Id], [System.Title], "
                "[System.WorkItemType], [System.State] "
                "FROM WorkItems "
                f"WHERE [System.TeamProject] = '{self.project}' "
                f"AND [System.Title] CONTAINS '{SEED_PREFIX}' "
                "ORDER BY [System.CreatedDate] ASC"
            )
        }

        response = self.session.post(
            url,
            params={"api-version": API_VERSION},
            json=wiql,
        )
        self._raise_with_details(response)

        ids = [
            item["id"]
            for item in response.json().get("workItems", [])
        ]

        if not ids:
            return []

        result = []

        for start in range(0, len(ids), 200):
            batch_ids = ids[start : start + 200]

            response = self.session.get(
                f"{self.base_url}/_apis/wit/workitems",
                params={
                    "ids": ",".join(str(item_id) for item_id in batch_ids),
                    "api-version": API_VERSION,
                    "$expand": "relations",
                },
            )
            self._raise_with_details(response)
            result.extend(response.json().get("value", []))

        return result

    def get_team_iterations(self) -> list[dict]:
        url = (
            f"{self.base_url}/{self.project}/{self.team}"
            "/_apis/work/teamsettings/iterations"
        )

        response = self.session.get(
            url,
            params={"api-version": API_VERSION},
        )
        self._raise_with_details(response)

        data = response.json()
        return data.get("values", data.get("value", []))

    def validate_sprints(self) -> dict[str, str]:
        iterations = self.get_team_iterations()

        required = {
            "Sprint 1": f"{self.project}\\Sprint 1",
            "Sprint 2": f"{self.project}\\Sprint 2",
            "Sprint 3": f"{self.project}\\Sprint 3",
        }

        by_path = {
            item.get("path"): item
            for item in iterations
        }

        result = {}

        for name, expected_path in required.items():
            node = by_path.get(expected_path)

            if node is None:
                available = sorted(
                    path
                    for path in by_path
                    if path
                )
                raise RuntimeError(
                    f"Required team iteration '{expected_path}' "
                    f"was not found. Available team iteration paths: "
                    f"{available}"
                )

            result[name] = expected_path

            print(
                f"  {name}: {expected_path} "
                f"(id={node.get('id')}, "
                f"start={node.get('start_date')}, "
                f"finish={node.get('finish_date')}, "
                f"time_frame={node.get('time_frame')})"
            )

        return result

    def create_work_item(
        self,
        work_item_type: str,
        title: str,
        iteration_path: str | None = None,
        story_points: float | None = None,
        parent_id: int | None = None,
    ) -> dict:
        url = (
            f"{self.base_url}/{self.project}"
            f"/_apis/wit/workitems/${work_item_type}"
        )

        operations = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"{SEED_PREFIX} {title}",
            }
        ]

        if iteration_path is not None:
            operations.append(
                {
                    "op": "add",
                    "path": "/fields/System.IterationPath",
                    "value": iteration_path,
                }
            )

        if story_points is not None:
            operations.append(
                {
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Scheduling.StoryPoints",
                    "value": story_points,
                }
            )

        if parent_id is not None:
            operations.append(
                {
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": (
                            f"{self.base_url}"
                            f"/_apis/wit/workItems/{parent_id}"
                        ),
                        "attributes": {
                            "comment": "AI Dashboard hierarchy",
                        },
                    },
                }
            )

        response = self.session.post(
            url,
            params={"api-version": API_VERSION},
            headers={
                "Content-Type": "application/json-patch+json",
            },
            json=operations,
        )
        self._raise_with_details(response)

        return response.json()

    def patch_work_item(
        self,
        work_item_id: int,
        operations: list[dict],
    ) -> dict:
        url = (
            f"{self.base_url}"
            f"/_apis/wit/workitems/{work_item_id}"
        )

        response = self.session.patch(
            url,
            params={"api-version": API_VERSION},
            headers={
                "Content-Type": "application/json-patch+json",
            },
            json=operations,
        )
        self._raise_with_details(response)

        return response.json()

    def update_state(
        self,
        work_item_id: int,
        state: str,
    ) -> dict:
        return self.patch_work_item(
            work_item_id,
            [
                {
                    "op": "add",
                    "path": "/fields/System.State",
                    "value": state,
                }
            ],
        )

    def delete_work_item(self, work_item_id: int) -> None:
        response = self.session.delete(
            f"{self.base_url}/_apis/wit/workitems/{work_item_id}",
            params={"api-version": API_VERSION},
        )
        self._raise_with_details(response)


def seed(
    client: AzureSeedClient,
    sprint_paths: dict[str, str],
) -> None:
    feature = client.create_work_item(
        "Feature",
        "AI Delivery Dashboard",
    )
    feature_id = feature["id"]

    print(f"Feature #{feature_id}: AI Delivery Dashboard")

    for story in STORY_DEFINITIONS:
        sprint_path = sprint_paths[story["sprint"]]

        story_item = client.create_work_item(
            "User Story",
            story["title"],
            iteration_path=sprint_path,
            story_points=story["story_points"],
            parent_id=feature_id,
        )
        story_id = story_item["id"]

        print(
            f"  Story #{story_id}: "
            f"{story['title']} "
            f"({story['story_points']} SP) "
            f"→ {story['sprint']} → New"
        )

        for task_title in story["tasks"]:
            task_item = client.create_work_item(
                "Task",
                task_title,
                iteration_path=sprint_path,
                parent_id=story_id,
            )
            print(
                f"    Task #{task_item['id']}: "
                f"{task_title} → New"
            )

        final_state = story["final_state"]

        if final_state == "Active":
            client.update_state(story_id, "Active")
            print(f"    Story #{story_id}: New → Active")

        elif final_state == "Closed":
            client.update_state(story_id, "Active")
            print(f"    Story #{story_id}: New → Active")

            time.sleep(1)

            client.update_state(story_id, "Closed")
            print(f"    Story #{story_id}: Active → Closed")


def main() -> None:
    client = AzureSeedClient()

    print("Azure DevOps 3-sprint seed")
    print(f"Organization: {client.organization}")
    print(f"Project:      {client.project}")
    print(f"Team:         {client.team}")
    print()

    existing = client.get_existing_seed_items()

    if existing:
        print(
            f"Found {len(existing)} existing "
            "AI Dashboard seed item(s)."
        )
        print("Removing old seed data...")

        for item in reversed(existing):
            client.delete_work_item(item["id"])
            print(f"  Deleted seed #{item['id']}")

        print()

    print("Validating existing team iterations...")
    sprint_paths = client.validate_sprints()
    print()

    print("Creating Feature → User Story → Task across 3 sprints...")
    print()

    seed(client, sprint_paths)

    print()
    print("Seed completed.")
    print()
    print("Expected planning metrics:")
    print("  Sprint 1: 26 committed / 13 completed / 50.0%")
    print("  Sprint 2: 21 committed / 21 completed / 100.0%")
    print("  Sprint 3: 24 committed / 8 completed / 33.33%")
    print("  Velocity average: 14.0 SP")


if __name__ == "__main__":
    main()

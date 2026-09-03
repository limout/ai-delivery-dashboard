from __future__ import annotations

import base64
import time

import requests

from app.core.config import settings


API_VERSION = "7.1"
SEED_PREFIX = "[AI Dashboard Seed]"


STORIES = [
    {
        "title": "Azure DevOps connector",
        "story_points": 8,
        "final_state": "Closed",
        "tasks": [
            "Implement connector",
            "Add authentication",
            "Add connector tests",
        ],
    },
    {
        "title": "Historical delivery metrics",
        "story_points": 5,
        "final_state": "Closed",
        "tasks": [
            "Historical API",
            "Metric calculations",
            "Dashboard charts",
        ],
    },
    {
        "title": "Insight Engine",
        "story_points": 8,
        "final_state": "Active",
        "tasks": [
            "Define delivery signals",
            "Risk detection",
        ],
    },
    {
        "title": "AI recommendations",
        "story_points": 5,
        "final_state": "New",
        "tasks": [
            "Ollama integration",
            "Recommendation prompt",
        ],
    },
]


class AzureSeedClient:
    def __init__(self):
        if not settings.azure_devops_org:
            raise ValueError("AZURE_DEVOPS_ORG is missing")

        if not settings.azure_devops_pat:
            raise ValueError("AZURE_DEVOPS_PAT is missing")

        if not settings.azure_devops_project:
            raise ValueError("AZURE_DEVOPS_PROJECT is missing")

        if not settings.azure_devops_team:
            raise ValueError("AZURE_DEVOPS_TEAM is missing")

        self.organization = settings.azure_devops_org
        self.project = settings.azure_devops_project
        self.team = settings.azure_devops_team
        self.base_url = f"https://dev.azure.com/{self.organization}"

        token = base64.b64encode(
            f":{settings.azure_devops_pat}".encode("utf-8")
        ).decode("ascii")

        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Authorization": f"Basic {token}",
        })

    def get_existing_seed_items(self) -> list[dict]:
        url = (
            f"{self.base_url}/{self.project}"
            "/_apis/wit/wiql"
        )

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
        response.raise_for_status()

        ids = [
            item["id"]
            for item in response.json().get("workItems", [])
        ]

        if not ids:
            return []

        result = []

        for start in range(0, len(ids), 200):
            batch_ids = ids[start:start + 200]

            response = self.session.get(
                f"{self.base_url}/_apis/wit/workitems",
                params={
                    "ids": ",".join(str(item_id) for item_id in batch_ids),
                    "api-version": API_VERSION,
                    "$expand": "relations",
                },
            )
            response.raise_for_status()
            result.extend(response.json().get("value", []))

        return result

    def get_sprint_path(self) -> str:
        url = (
            f"{self.base_url}/{self.project}/"
            f"{self.team}/_apis/work/teamsettings/iterations"
        )

        response = self.session.get(
            url,
            params={"api-version": API_VERSION},
        )
        response.raise_for_status()

        iterations = response.json().get("value", [])

        for iteration in iterations:
            if iteration.get("name") == "Sprint 1":
                return iteration["path"]

        raise RuntimeError(
            "Sprint 1 was not found. "
            "Create Sprint 1 in Azure DevOps first."
        )

    def create_work_item(
        self,
        work_item_type: str,
        title: str,
        fields: dict[str, object] | None = None,
        parent_id: int | None = None,
    ) -> dict:
        url = (
            f"{self.base_url}/{self.project}"
            f"/_apis/wit/workitems/${work_item_type}"
        )

        payload = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"{SEED_PREFIX} {title}",
            }
        ]

        for field, value in (fields or {}).items():
            payload.append({
                "op": "add",
                "path": f"/fields/{field}",
                "value": value,
            })

        if parent_id is not None:
            payload.append({
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": (
                        f"{self.base_url}/_apis/wit/workItems/"
                        f"{parent_id}"
                    ),
                    "attributes": {
                        "comment": "AI Dashboard hierarchy",
                    },
                },
            })

        response = self.session.post(
            url,
            params={"api-version": API_VERSION},
            headers={
                "Content-Type": "application/json-patch+json",
            },
            json=payload,
        )
        response.raise_for_status()

        return response.json()

    def update_state(self, work_item_id: int, state: str) -> dict:
        url = (
            f"{self.base_url}/_apis/wit/workitems/"
            f"{work_item_id}"
        )

        payload = [
            {
                "op": "add",
                "path": "/fields/System.State",
                "value": state,
            }
        ]

        response = self.session.patch(
            url,
            params={"api-version": API_VERSION},
            headers={
                "Content-Type": "application/json-patch+json",
            },
            json=payload,
        )
        response.raise_for_status()

        return response.json()

    def delete_work_item(self, work_item_id: int) -> None:
        url = (
            f"{self.base_url}/_apis/wit/workitems/"
            f"{work_item_id}"
        )

        response = self.session.delete(
            url,
            params={"api-version": API_VERSION},
        )
        response.raise_for_status()

    def get_work_item(self, work_item_id: int) -> dict:
        response = self.session.get(
            f"{self.base_url}/_apis/wit/workitems/{work_item_id}",
            params={
                "api-version": API_VERSION,
                "$expand": "relations",
            },
        )
        response.raise_for_status()
        return response.json()


def seed(client: AzureSeedClient, sprint_path: str) -> None:
    feature = client.create_work_item(
        "Feature",
        "AI Delivery Dashboard",
        {
            "System.IterationPath": sprint_path,
        },
    )

    feature_id = feature["id"]

    print(f"Feature #{feature_id}: AI Delivery Dashboard")

    for story in STORIES:
        story_item = client.create_work_item(
            "User Story",
            story["title"],
            {
                "System.IterationPath": sprint_path,
                "Microsoft.VSTS.Scheduling.StoryPoints": (
                    story["story_points"]
                ),
            },
            parent_id=feature_id,
        )

        story_id = story_item["id"]

        print(
            f"  Story #{story_id}: "
            f"{story['title']} "
            f"({story['story_points']} SP) → New"
        )

        for task_title in story["tasks"]:
            task_item = client.create_work_item(
                "Task",
                task_title,
                {
                    "System.IterationPath": sprint_path,
                },
                parent_id=story_id,
            )

            print(
                f"    Task #{task_item['id']}: {task_title} → New"
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


def print_hierarchy(client: AzureSeedClient, items: list[dict]) -> None:
    by_id = {item["id"]: item for item in items}

    print()
    print("CREATED HIERARCHY")
    print("=" * 60)

    for item in items:
        fields = item.get("fields", {})
        item_type = fields.get("System.WorkItemType")
        title = fields.get("System.Title", "")
        state = fields.get("System.State")
        iteration = fields.get("System.IterationPath")
        points = fields.get("Microsoft.VSTS.Scheduling.StoryPoints")

        parent_id = None

        for relation in item.get("relations", []):
            if relation.get("rel") != "System.LinkTypes.Hierarchy-Reverse":
                continue

            relation_url = relation.get("url", "")
            marker = "/workItems/"
            if marker in relation_url:
                parent_id = int(
                    relation_url.rsplit(marker, 1)[1]
                )

        indent = {
            "Feature": "",
            "User Story": "  ",
            "Task": "    ",
        }.get(item_type, "")

        points_text = f" | {points} SP" if points is not None else ""

        parent_text = (
            f" | parent=#{parent_id}"
            if parent_id is not None
            else ""
        )

        print(
            f"{indent}{item_type}: #{item['id']} "
            f"{title} | {state}{points_text}"
            f"{parent_text}"
        )

    print()
    print("SPRINT / ITERATION")
    print("=" * 60)

    for item in items:
        fields = item.get("fields", {})
        print(
            f"#{item['id']} "
            f"{fields.get('System.WorkItemType')}: "
            f"{fields.get('System.IterationPath')}"
        )


def main() -> None:
    client = AzureSeedClient()

    print("Azure DevOps hierarchy seed")
    print(f"Organization: {client.organization}")
    print(f"Project:      {client.project}")
    print(f"Team:         {client.team}")
    print()

    existing = client.get_existing_seed_items()

    if existing:
        existing_types = {
            item.get("fields", {}).get("System.WorkItemType")
            for item in existing
        }

        if existing_types <= {"Task"}:
            print(
                f"Found {len(existing)} old flat seed task(s)."
            )
            print("Removing only the old AI Dashboard seed data...")

            for item in existing:
                work_item_id = item["id"]
                client.delete_work_item(work_item_id)
                print(f"  Deleted old seed #{work_item_id}")

            print()
        else:
            print(
                "Hierarchy seed already exists. "
                "Nothing will be created."
            )
            print(
                "Existing seed types: "
                f"{sorted(existing_types)}"
            )
            return

    sprint_path = client.get_sprint_path()

    print(f"Sprint: {sprint_path}")
    print()
    print("Creating Feature → User Story → Task...")
    print()

    seed(client, sprint_path)

    print()
    print("Seed completed.")
    print()
    print("Expected commitment: 26 SP")
    print("Done: 13 SP")
    print("In Progress: 8 SP")
    print("New: 5 SP")


if __name__ == "__main__":
    main()

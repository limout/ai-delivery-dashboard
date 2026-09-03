from __future__ import annotations

import requests
from requests.auth import HTTPBasicAuth

from app.core.config import settings


API_VERSION = "3"


def main() -> None:
    if not settings.jira_url:
        raise ValueError("JIRA_URL is missing")

    if not settings.jira_email:
        raise ValueError("JIRA_EMAIL is missing")

    if not settings.jira_api_token:
        raise ValueError("JIRA_API_TOKEN is missing")

    project_key = "KAN"

    base_url = settings.jira_url.rstrip("/")

    auth = HTTPBasicAuth(
        settings.jira_email,
        settings.jira_api_token,
    )

    headers = {
        "Accept": "application/json",
    }

    print("Jira project structure")
    print(f"URL:     {base_url}")
    print(f"Project: {project_key}")
    print()

    # ---------------------------------------------------------
    # 1. Project information
    # ---------------------------------------------------------

    response = requests.get(
        f"{base_url}/rest/api/{API_VERSION}/project/{project_key}",
        auth=auth,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    project = response.json()

    project_id = project["id"]

    print("PROJECT")
    print("=" * 60)
    print(f"ID:       {project_id}")
    print(f"Key:      {project.get('key')}")
    print(f"Name:     {project.get('name')}")
    print(f"Type:     {project.get('projectTypeKey')}")
    print(f"Simplified:{project.get('simplified')}")
    print()

    # ---------------------------------------------------------
    # 2. Issue types + statuses
    # ---------------------------------------------------------

    response = requests.get(
        f"{base_url}/rest/api/{API_VERSION}"
        f"/project/{project_key}/statuses",
        auth=auth,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    statuses = response.json()

    print("ISSUE TYPES AND STATUSES")
    print("=" * 60)

    for issue_type in statuses:
        print(
            f"\n{issue_type.get('name')} "
            f"(id={issue_type.get('id')}, "
            f"subtask={issue_type.get('subtask')})"
        )

        for status in issue_type.get("statuses", []):
            print(
                f"  - {status.get('name')} "
                f"(id={status.get('id')})"
            )

    print()

    # ---------------------------------------------------------
    # 3. Project hierarchy
    # ---------------------------------------------------------

    response = requests.get(
        f"{base_url}/rest/api/{API_VERSION}"
        f"/project/{project_id}/hierarchy",
        auth=auth,
        headers=headers,
        timeout=30,
    )

    if response.status_code == 404:
        print("HIERARCHY")
        print("=" * 60)
        print("Project hierarchy endpoint is not available for this project.")
        print()
        return

    response.raise_for_status()

    hierarchy = response.json()

    print("HIERARCHY")
    print("=" * 60)

    for level in sorted(
        hierarchy.get("hierarchy", []),
        key=lambda item: item.get("level", 0),
        reverse=True,
    ):
        print(
            f"\nLevel {level.get('level')}: "
            f"{level.get('name')}"
        )

        for issue_type in level.get("issueTypes", []):
            print(
                f"  - {issue_type.get('name')} "
                f"(id={issue_type.get('id')})"
            )

    print()
    print("No Jira data was created or modified.")


if __name__ == "__main__":
    main()
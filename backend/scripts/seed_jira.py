import time

import requests

from app.core.config import settings


SEED_PREFIX = "[AI Dashboard Seed]"


class JiraSeedClient:
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

    def search(self, jql: str) -> list[dict]:
        response = self.session.get(
            f"{self.base_url}/rest/api/3/search/jql",
            params={
                "jql": jql,
                "maxResults": 100,
                "fields": "summary,issuetype,parent",
            },
        )
        response.raise_for_status()
        return response.json().get("issues", [])

    def create_issue(
        self,
        project: str,
        issue_type: str,
        summary: str,
        parent_key: str | None = None,
    ) -> str:
        fields = {
            "project": {"key": project},
            "summary": f"{SEED_PREFIX} {summary}",
            "issuetype": {"name": issue_type},
        }

        if parent_key:
            fields["parent"] = {"key": parent_key}

        response = self.session.post(
            f"{self.base_url}/rest/api/3/issue",
            json={"fields": fields},
        )

        if not response.ok:
            print()
            print("JIRA ERROR")
            print(response.status_code)
            print(response.text)
            print()
            response.raise_for_status()

        issue_key = response.json()["key"]

        print(
            f"CREATED {issue_key:8} | "
            f"{issue_type:8} | "
            f"{summary}"
        )

        return issue_key

    def transition_issue(
        self,
        issue_key: str,
        target_status: str,
    ) -> None:
        response = self.session.get(
            f"{self.base_url}/rest/api/3/issue/"
            f"{issue_key}/transitions",
        )
        response.raise_for_status()

        transitions = response.json().get("transitions", [])

        transition_id = None

        for transition in transitions:
            if transition.get("to", {}).get("name") == target_status:
                transition_id = transition["id"]
                break

        if transition_id is None:
            print(
                f"WARNING: cannot transition "
                f"{issue_key} to {target_status}"
            )
            return

        response = self.session.post(
            f"{self.base_url}/rest/api/3/issue/"
            f"{issue_key}/transitions",
            json={
                "transition": {
                    "id": transition_id,
                }
            },
        )
        response.raise_for_status()

        print(
            f"UPDATED  {issue_key:8} | "
            f"status={target_status}"
        )

    def delete_issue(self, issue_key: str) -> None:
        response = self.session.delete(
            f"{self.base_url}/rest/api/3/issue/{issue_key}",
        )

        response.raise_for_status()

        print(f"DELETED  {issue_key}")

    def delete_old_seed(self, project: str) -> None:
        issues = self.search(
            f'project = {project} AND summary ~ '
            f'"{SEED_PREFIX}" ORDER BY created DESC'
        )

        if not issues:
            print("No previous AI Dashboard Seed issues found.")
            return

        print()
        print("Removing previous AI Dashboard Seed issues...")

        # Delete children first.
        issues = sorted(
            issues,
            key=lambda issue: self._depth(issue),
            reverse=True,
        )

        for issue in issues:
            self.delete_issue(issue["key"])
            time.sleep(0.2)

    @staticmethod
    def _depth(issue: dict) -> int:
        parent = issue.get("fields", {}).get("parent")

        if parent:
            return 1

        return 0


def main():
    project = "KAN"

    client = JiraSeedClient()

    print()
    print("=" * 80)
    print("JIRA AI DASHBOARD SEED")
    print("=" * 80)

    client.delete_old_seed(project)

    print()
    print("Creating hierarchy...")
    print()

    # ---------------------------------------------------------
    # Epic
    # ---------------------------------------------------------

    epic = client.create_issue(
        project=project,
        issue_type="Epic",
        summary="AI Delivery Dashboard",
    )

    # ---------------------------------------------------------
    # Feature
    #
    # Jira project hierarchy shows Feature at the base level,
    # so it is a direct child of the Epic.
    # ---------------------------------------------------------

    feature = client.create_issue(
        project=project,
        issue_type="Feature",
        summary="Delivery Intelligence",
        parent_key=epic,
    )

    # ---------------------------------------------------------
    # Story 1
    #
    # Story is also a base-level issue type, therefore it is
    # a direct child of the Epic rather than the Feature.
    #
    # Story Points are intentionally NOT set:
    # this Jira project has no Story Points field configured.
    # ---------------------------------------------------------

    story_1 = client.create_issue(
        project=project,
        issue_type="Story",
        summary="Normalize delivery data",
        parent_key=epic,
    )

    subtask_1 = client.create_issue(
        project=project,
        issue_type="Subtask",
        summary="Implement normalized work item model",
        parent_key=story_1,
    )

    subtask_2 = client.create_issue(
        project=project,
        issue_type="Subtask",
        summary="Add source hierarchy mapping",
        parent_key=story_1,
    )

    # ---------------------------------------------------------
    # Story 2
    # ---------------------------------------------------------

    story_2 = client.create_issue(
        project=project,
        issue_type="Story",
        summary="Historical delivery metrics",
        parent_key=epic,
    )

    subtask_3 = client.create_issue(
        project=project,
        issue_type="Subtask",
        summary="Calculate historical WIP",
        parent_key=story_2,
    )

    subtask_4 = client.create_issue(
        project=project,
        issue_type="Subtask",
        summary="Build historical charts",
        parent_key=story_2,
    )

    # ---------------------------------------------------------
    # Bug
    #
    # Bug is also a base-level issue type.
    # ---------------------------------------------------------

    bug = client.create_issue(
        project=project,
        issue_type="Bug",
        summary="Fix metric data quality edge case",
        parent_key=epic,
    )

    # ---------------------------------------------------------
    # Statuses
    # ---------------------------------------------------------

    print()
    print("Setting statuses...")
    print()

    # Epic completed.
    client.transition_issue(
        epic,
        "Done",
    )

    # Feature is currently being worked on.
    client.transition_issue(
        feature,
        "In Progress",
    )

    # Story 1 completed.
    client.transition_issue(
        story_1,
        "Done",
    )

    client.transition_issue(
        subtask_1,
        "Done",
    )

    client.transition_issue(
        subtask_2,
        "Done",
    )

    # Story 2 is currently in progress.
    client.transition_issue(
        story_2,
        "In Progress",
    )

    client.transition_issue(
        subtask_3,
        "Done",
    )

    client.transition_issue(
        subtask_4,
        "In Progress",
    )

    # Bug is also in progress.
    client.transition_issue(
        bug,
        "In Progress",
    )

    print()
    print("=" * 80)
    print("SEED COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    jira_url: str = os.getenv("JIRA_URL", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")

    azure_devops_org: str = os.getenv("AZURE_DEVOPS_ORG", "")
    azure_devops_project: str = os.getenv("AZURE_DEVOPS_PROJECT", "")
    azure_devops_pat: str = os.getenv("AZURE_DEVOPS_PAT", "")
    azure_devops_team: str = os.getenv("AZURE_DEVOPS_TEAM", "")


settings = Settings()

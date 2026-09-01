import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    jira_url: str = os.getenv("JIRA_URL", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")


settings = Settings()
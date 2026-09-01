from datetime import datetime

from pydantic import BaseModel


class WorkItem(BaseModel):
    id: str
    source: str
    project: str
    type: str
    title: str

    status: str | None = None
    priority: str | None = None
    assignee: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None
    due_date: datetime | None = None

    iteration: str | None = None
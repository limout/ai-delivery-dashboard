from datetime import datetime

from pydantic import BaseModel


class WorkItemHistory(BaseModel):
    work_item_id: str
    timestamp: datetime
    field: str
    from_value: str | None = None
    to_value: str | None = None
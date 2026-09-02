from pydantic import BaseModel


class DataQuality(BaseModel):
    status: str
    message: str
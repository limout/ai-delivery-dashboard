from abc import ABC, abstractmethod

from app.core.models.work_item import WorkItem


class Metric(ABC):
    name: str
    description: str
    category: str
    required_data: str

    @abstractmethod
    def calculate(self, data) -> dict:
        """Calculate this metric from the required data."""
        raise NotImplementedError
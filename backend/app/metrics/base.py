from abc import ABC, abstractmethod

from app.core.models.work_item import WorkItem


class Metric(ABC):
    name: str
    description: str
    category: str

    @abstractmethod
    def calculate(self, work_items: list[WorkItem]) -> dict:
        """Calculate this metric from normalized work items."""
        raise NotImplementedError
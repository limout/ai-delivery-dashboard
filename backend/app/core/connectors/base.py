from abc import ABC, abstractmethod

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory


class DeliveryConnector(ABC):

    @abstractmethod
    def get_projects(self) -> list[dict]:
        """Return available projects."""
        raise NotImplementedError

    @abstractmethod
    def get_work_items(self, project: str) -> list[WorkItem]:
        """Return normalized work items for a project."""
        raise NotImplementedError

    @abstractmethod
    def get_work_item_history(
        self,
        work_item_id: str,
    ) -> list[WorkItemHistory]:
        """Return normalized change history for a work item."""
        raise NotImplementedError

    @abstractmethod
    def get_iterations(self, project: str) -> list[dict]:
        """Return iterations/sprints for a project."""
        raise NotImplementedError

    @abstractmethod
    def get_releases(self, project: str) -> list[dict]:
        """Return releases/versions for a project."""
        raise NotImplementedError

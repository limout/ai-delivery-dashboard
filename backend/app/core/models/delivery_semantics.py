from enum import Enum


class DeliveryRole(str, Enum):
    CONTAINER = "container"
    PLANNING_ITEM = "planning_item"
    EXECUTION_ITEM = "execution_item"
    DEFECT = "defect"
    UNKNOWN = "unknown"


JIRA_ROLE_MAPPING = {
    "Epic": DeliveryRole.CONTAINER,
    "Feature": DeliveryRole.PLANNING_ITEM,
    "Story": DeliveryRole.PLANNING_ITEM,
    "Task": DeliveryRole.EXECUTION_ITEM,
    "Subtask": DeliveryRole.EXECUTION_ITEM,
    "Bug": DeliveryRole.DEFECT,
}


def get_delivery_role(
    source: str,
    work_item_type: str,
) -> DeliveryRole:
    if source.lower() == "jira":
        return JIRA_ROLE_MAPPING.get(
            work_item_type,
            DeliveryRole.UNKNOWN,
        )

    return DeliveryRole.UNKNOWN
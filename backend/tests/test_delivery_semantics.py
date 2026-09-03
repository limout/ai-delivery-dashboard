from app.core.models.delivery_semantics import (
    DeliveryRole,
    get_delivery_role,
)


def test_jira_epic_is_container():
    assert get_delivery_role("jira", "Epic") == DeliveryRole.CONTAINER


def test_jira_feature_is_planning_item():
    assert get_delivery_role("jira", "Feature") == DeliveryRole.PLANNING_ITEM


def test_jira_story_is_planning_item():
    assert get_delivery_role("jira", "Story") == DeliveryRole.PLANNING_ITEM


def test_jira_task_is_execution_item():
    assert get_delivery_role("jira", "Task") == DeliveryRole.EXECUTION_ITEM


def test_jira_subtask_is_execution_item():
    assert get_delivery_role("jira", "Subtask") == DeliveryRole.EXECUTION_ITEM


def test_jira_bug_is_defect():
    assert get_delivery_role("jira", "Bug") == DeliveryRole.DEFECT


def test_unknown_jira_type_is_unknown():
    assert get_delivery_role("jira", "SomethingNew") == DeliveryRole.UNKNOWN


def test_non_jira_source_is_unknown_for_now():
    assert get_delivery_role("azure_devops", "User Story") == DeliveryRole.UNKNOWN
from app.connectors.jira.connector import JiraConnector


def test_jira_connector_reads_work_items():
    connector = JiraConnector()

    items = connector.get_work_items("KAN")

    assert len(items) > 0

    item = items[0]

    assert item.source == "jira"
    assert item.project == "KAN"
    assert item.id.startswith("KAN-")
    assert item.title
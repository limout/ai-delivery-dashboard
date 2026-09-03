from datetime import date, datetime, timezone

from app.core.models.work_item import WorkItem
from app.core.models.work_item_history import WorkItemHistory
from app.metrics.historical import HistoricalMetrics


def make_item(
    item_id: str,
    created_at: str = "2026-09-01T09:00:00+00:00",
    status: str = "In Progress",
) -> WorkItem:
    return WorkItem(
        id=item_id,
        source="azure_devops",
        project="KAN",
        type="User Story",
        title=f"Story {item_id}",
        status=status,
        created_at=datetime.fromisoformat(created_at),
    )


def history(
    item_id: str,
    timestamp: str,
    from_value: str,
    to_value: str,
) -> WorkItemHistory:
    return WorkItemHistory(
        work_item_id=item_id,
        timestamp=datetime.fromisoformat(timestamp),
        field="System.State",
        from_value=from_value,
        to_value=to_value,
    )


def test_wip_reconstructs_status_by_day():
    metric = HistoricalMetrics()

    items = [
        make_item("1"),
        make_item("2", status="Done"),
    ]

    histories = [
        history(
            "1",
            "2026-09-02T10:00:00+00:00",
            "New",
            "In Progress",
        ),
        history(
            "1",
            "2026-09-04T10:00:00+00:00",
            "In Progress",
            "Done",
        ),
        history(
            "2",
            "2026-09-02T11:00:00+00:00",
            "New",
            "In Progress",
        ),
        history(
            "2",
            "2026-09-03T11:00:00+00:00",
            "In Progress",
            "Done",
        ),
    ]

    result = metric.calculate_wip(
        work_items=items,
        histories=histories,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 5),
    )

    values = [point["value"] for point in result["points"]]

    assert values == [0, 2, 1, 1, 0]


def test_throughput_counts_done_transitions_per_day():
    metric = HistoricalMetrics()

    items = [
        make_item("1"),
        make_item("2"),
    ]

    histories = [
        history(
            "1",
            "2026-09-03T10:00:00+00:00",
            "In Progress",
            "Done",
        ),
        history(
            "2",
            "2026-09-03T14:00:00+00:00",
            "In Progress",
            "Done",
        ),
    ]

    result = metric.calculate_throughput(
        work_items=items,
        histories=histories,
        start_date=date(2026, 9, 2),
        end_date=date(2026, 9, 4),
    )

    assert [point["value"] for point in result["points"]] == [0, 2, 0]


def test_cycle_time_is_measured_from_in_progress_to_done():
    metric = HistoricalMetrics()

    items = [make_item("1")]

    histories = [
        history(
            "1",
            "2026-09-02T10:00:00+00:00",
            "New",
            "In Progress",
        ),
        history(
            "1",
            "2026-09-04T10:00:00+00:00",
            "In Progress",
            "Done",
        ),
    ]

    result = metric.calculate_cycle_time(
        work_items=items,
        histories=histories,
        start_date=date(2026, 9, 4),
        end_date=date(2026, 9, 4),
    )

    assert result["points"][0]["value"] == 2.0
    assert result["points"][0]["sample_size"] == 1


def test_lead_time_is_measured_from_creation_to_done():
    metric = HistoricalMetrics()

    items = [
        make_item(
            "1",
            created_at="2026-09-01T10:00:00+00:00",
        )
    ]

    histories = [
        history(
            "1",
            "2026-09-02T10:00:00+00:00",
            "New",
            "In Progress",
        ),
        history(
            "1",
            "2026-09-04T10:00:00+00:00",
            "In Progress",
            "Done",
        ),
    ]

    result = metric.calculate_lead_time(
        work_items=items,
        histories=histories,
        start_date=date(2026, 9, 4),
        end_date=date(2026, 9, 4),
    )

    assert result["points"][0]["value"] == 3.0
    assert result["points"][0]["sample_size"] == 1


def test_empty_days_are_null_for_duration_metrics():
    metric = HistoricalMetrics()

    result = metric.calculate_lead_time(
        work_items=[],
        histories=[],
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 2),
    )

    assert [point["value"] for point in result["points"]] == [
        None,
        None,
    ]


def test_calculate_rejects_unsupported_metric():
    metric = HistoricalMetrics()

    try:
        metric.calculate(
            metric="velocity",
            work_items=[],
            histories=[],
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 1),
        )
    except ValueError as exc:
        assert "Unsupported historical metric" in str(exc)
    else:
        raise AssertionError("Expected ValueError")

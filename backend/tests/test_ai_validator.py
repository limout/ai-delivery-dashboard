from app.ai.context import AIContext
from app.ai.response import AIStructuredResponse
from app.ai.validator import AIResponseValidator


def test_validator_accepts_good_metric_not_in_data_gaps():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={
            "lead_time": {
                "value": 0,
                "data_quality": {"status": "good"},
            }
        },
    )

    response = AIStructuredResponse(
        risk={"title": "WIP congestion", "severity": "high"},
        facts=["WIP is 9"],
        interpretation=["The system may be accumulating work."],
        recommendations=["Review aging work."],
        data_gaps=[],
    )

    assert AIResponseValidator().validate(response, context) == response


def test_validator_rejects_good_metric_reported_as_data_gap():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={
            "lead_time": {
                "value": 0,
                "data_quality": {"status": "good"},
            }
        },
    )

    response = AIStructuredResponse(
        risk={"title": "WIP congestion", "severity": "high"},
        facts=["WIP is 9"],
        interpretation=[],
        recommendations=[],
        data_gaps=["Lead time has limited historical data points"],
    )

    try:
        AIResponseValidator().validate(response, context)
        assert False, "Expected validation error"
    except ValueError as exc:
        assert "lead_time" in str(exc)


def test_validator_accepts_insufficient_metric_as_data_gap():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        metrics={
            "cycle_time": {
                "value": None,
                "data_quality": {"status": "insufficient_data"},
            }
        },
    )

    response = AIStructuredResponse(
        risk={"title": "WIP congestion", "severity": "high"},
        facts=["WIP is 9"],
        interpretation=[],
        recommendations=[],
        data_gaps=["Cycle time is unavailable"],
    )

    assert AIResponseValidator().validate(response, context) == response


def test_validator_rejects_unknown_work_item():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        insights=[
            {
                "id": "wip-congestion",
                "evidence": {
                    "wip_items": [{"id": "KAN-3", "title": "Fix bug"}]
                },
            }
        ],
    )

    response = AIStructuredResponse(
        risk={"title": "WIP congestion", "severity": "high"},
        facts=["KAN-999 is blocked"],
        interpretation=[],
        recommendations=[],
        data_gaps=[],
    )

    with __import__("pytest").raises(ValueError, match="KAN-999"):
        AIResponseValidator().validate(response, context)


def test_validator_accepts_known_work_item():
    context = AIContext(
        project="KAN",
        source="jira",
        analysis_window_days=14,
        insights=[
            {
                "id": "wip-congestion",
                "evidence": {
                    "wip_items": [{"id": "KAN-3", "title": "Fix bug"}]
                },
            }
        ],
    )

    response = AIStructuredResponse(
        risk={"title": "WIP congestion", "severity": "high"},
        facts=["KAN-3 is aging in progress"],
        interpretation=[],
        recommendations=["Review KAN-3"],
        data_gaps=[],
    )

    assert AIResponseValidator().validate(response, context) == response

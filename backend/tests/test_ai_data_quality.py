from app.ai.context import AIContextBuilder
from app.ai.response import AIStructuredResponse
from app.ai.validator import AIResponseValidator


def test_context_builder_marks_only_deterministically_unavailable_metrics_as_gaps():
    analysis = {
        "project": "KAN",
        "days": 14,
        "metrics": {
            "wip": {
                "value": 2,
                "data_quality": {"status": "good"},
            },
            "velocity": {
                "value": 14,
                "status": "ok",
                "iterations": {
                    "Sprint 1": {"completed": 13},
                    "Sprint 2": {"completed": 21},
                    "Sprint 3": {"completed": 8},
                },
            },
            "cycle_time": {
                "value": None,
                "data_quality": {"status": "insufficient_data"},
            },
        },
        "historical": {
            "velocity": {
                "status": "ok",
                "points": [
                    {"label": "Sprint 1", "value": 13},
                    {"label": "Sprint 2", "value": 21},
                    {"label": "Sprint 3", "value": 8},
                ],
            }
        },
        "insights": [],
    }

    context = AIContextBuilder().build(analysis, source="azure_devops")

    assert context.data_gaps == ["cycle_time"]


def test_validator_rejects_unimplemented_metrics_as_data_gaps():
    context = AIContextBuilder().build(
        {
            "project": "KAN",
            "days": 14,
            "metrics": {
                "wip": {
                    "value": 2,
                    "data_quality": {"status": "good"},
                }
            },
            "historical": {},
            "insights": [],
        },
        source="azure_devops",
    )

    response = AIStructuredResponse(
        risk={"title": "WIP", "severity": "high"},
        facts=[],
        interpretation=[],
        recommendations=[],
        data_gaps=["No defect rate metrics"],
    )

    try:
        AIResponseValidator().validate(response, context)
    except ValueError as exc:
        assert "unsupported data gap" in str(exc)
    else:
        raise AssertionError("Expected unsupported data gap validation error")


def test_validator_rejects_commitment_metric_described_as_work_items():
    context = AIContextBuilder().build(
        {
            "project": "KAN",
            "days": 14,
            "metrics": {
                "commitment_vs_completed": {
                    "value": 61.11,
                    "unit": "percent",
                    "status": "ok",
                }
            },
            "historical": {},
            "insights": [],
        },
        source="azure_devops",
    )

    response = AIStructuredResponse(
        risk={"title": "Planning risk", "severity": "high"},
        facts=["Only 61% of committed work items were completed."],
        interpretation=[],
        recommendations=[],
        data_gaps=[],
    )

    try:
        AIResponseValidator().validate(response, context)
    except ValueError as exc:
        assert "Story Points" in str(exc)
    else:
        raise AssertionError("Expected metric unit validation error")

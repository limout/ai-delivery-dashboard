from app.ai.context import AIContextBuilder


def test_build_preserves_deterministic_delivery_context():
    analysis = {
        "project": "KAN",
        "days": 14,
        "metrics": {
            "wip": {
                "value": 9,
                "unit": "items",
                "data_quality": {
                    "status": "good",
                    "message": "Sufficient data available.",
                },
            },
            "velocity": {
                "value": 14,
                "unit": "story_points",
            },
        },
        "historical": {
            "wip": {
                "metric": "wip",
                "unit": "items",
                "status": "ok",
                "points": [
                    {"date": "2026-09-03", "value": 9},
                ],
            },
            "velocity": {
                "metric": "velocity",
                "unit": "story_points",
                "status": "ok",
                "points": [
                    {"iteration": "Sprint 2", "value": 16},
                    {"iteration": "Sprint 3", "value": 14},
                ],
            },
        },
        "insights": [
            {
                "id": "wip-congestion",
                "severity": "high",
                "title": "WIP is increasing without higher throughput",
                "fact": "WIP is 9.",
                "signal": "Work may be accumulating.",
                "recommendation": "Review aging work.",
                "confidence": "medium",
                "metric": "wip",
                "evidence": {
                    "wip_count": 9,
                    "blocked_count": 0,
                    "wip_items": [],
                    "blocked_items": [],
                },
            }
        ],
    }

    context = AIContextBuilder().build(
        analysis=analysis,
        source="azure_devops",
    )

    assert context.project == "KAN"
    assert context.source == "azure_devops"
    assert context.analysis_window_days == 14

    assert context.metrics["wip"]["value"] == 9
    assert context.metrics["velocity"]["value"] == 14

    assert context.historical["velocity"]["points"][1]["value"] == 14

    assert len(context.insights) == 1
    assert context.insights[0]["severity"] == "high"
    assert context.insights[0]["evidence"]["wip_count"] == 9


def test_build_does_not_invent_missing_data():
    analysis = {
        "project": "KAN",
        "days": 14,
        "metrics": {
            "cycle_time": {
                "value": None,
                "unit": "days",
                "sample_size": 0,
                "data_quality": {
                    "status": "insufficient_data",
                    "message": "No completed cycles.",
                },
            }
        },
        "historical": {
            "cycle_time": {
                "metric": "cycle_time",
                "unit": "days",
                "status": "ok",
                "points": [
                    {"date": "2026-09-03", "value": None},
                ],
            }
        },
        "insights": [],
    }

    context = AIContextBuilder().build(
        analysis=analysis,
        source="jira",
    )

    assert context.metrics["cycle_time"]["value"] is None
    assert context.metrics["cycle_time"]["data_quality"]["status"] == "insufficient_data"
    assert context.historical["cycle_time"]["points"][0]["value"] is None
    assert context.insights == []


def test_build_ignores_invalid_top_level_values_without_creating_fake_facts():
    analysis = {
        "project": "KAN",
        "days": 14,
        "metrics": None,
        "historical": "not-a-dict",
        "insights": [
            {"title": "Valid insight"},
            "not an insight",
            None,
        ],
    }

    context = AIContextBuilder().build(
        analysis=analysis,
        source="jira",
    )

    assert context.metrics == {}
    assert context.historical == {}
    assert context.insights == [{"title": "Valid insight"}]

def test_ai_context_preserves_structured_insight_evidence():
    analysis = {
        "project": "KAN",
        "days": 14,
        "metrics": {},
        "historical": {},
        "insights": [
            {
                "id": "wip-congestion",
                "severity": "high",
                "title": "WIP is increasing without higher throughput",
                "fact": "WIP is 9.",
                "signal": "Potential congestion.",
                "recommendation": "Review aging work.",
                "confidence": "medium",
                "metric": "wip",
                "evidence": {
                    "wip": {
                        "current": 9,
                        "trend": 4,
                    },
                    "throughput": {
                        "current": 7,
                        "trend": -1,
                    },
                },
            }
        ],
    }

    context = AIContextBuilder().build(
        analysis=analysis,
        source="jira",
    )

    insight = context.insights[0]

    assert insight["evidence"]["wip"]["current"] == 9
    assert insight["evidence"]["wip"]["trend"] == 4
    assert insight["evidence"]["throughput"]["current"] == 7
    assert insight["evidence"]["throughput"]["trend"] == -1
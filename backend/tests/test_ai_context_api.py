from fastapi.testclient import TestClient

import app.main as main_module


def test_ai_context_endpoint_builds_context_from_existing_insights_pipeline(
    monkeypatch,
):
    analysis = {
        "project": "KAN",
        "days": 14,
        "metrics": {
            "wip": {
                "value": 9,
                "unit": "items",
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

    def fake_project_insights(project, source="jira", days=14):
        assert project == "KAN"
        assert source == "azure_devops"
        assert days == 14
        return analysis

    monkeypatch.setattr(
        main_module,
        "project_insights",
        fake_project_insights,
    )

    client = TestClient(main_module.app)

    response = client.get(
        "/projects/KAN/ai/context",
        params={
            "source": "azure_devops",
            "days": 14,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["project"] == "KAN"
    assert body["source"] == "azure_devops"
    assert body["analysis_window_days"] == 14
    assert body["metrics"]["wip"]["value"] == 9
    assert body["historical"]["wip"]["points"][0]["value"] == 9
    assert body["insights"][0]["severity"] == "high"


def test_ai_context_endpoint_does_not_invent_missing_data(monkeypatch):
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

    monkeypatch.setattr(
        main_module,
        "project_insights",
        lambda project, source="jira", days=14: analysis,
    )

    client = TestClient(main_module.app)

    response = client.get("/projects/KAN/ai/context")

    assert response.status_code == 200

    body = response.json()

    assert body["metrics"]["cycle_time"]["value"] is None
    assert (
        body["metrics"]["cycle_time"]["data_quality"]["status"]
        == "insufficient_data"
    )
    assert body["historical"]["cycle_time"]["points"][0]["value"] is None
    assert body["insights"] == []

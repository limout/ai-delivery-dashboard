from app.services.insight import InsightEngine


def test_wip_congestion_insight():
    engine = InsightEngine()
    metrics = {
        "wip": {"value": 14},
        "throughput": {"value": 5},
    }
    historical = {
        "wip": {"points": [{"value": 8}, {"value": 14}]},
        "throughput": {"points": [{"value": 6}, {"value": 5}]},
    }

    result = engine.analyze(metrics, historical)

    assert result[0]["id"] == "wip-congestion"
    assert result[0]["severity"] == "high"
    assert result[0]["confidence"] == "medium"


def test_cycle_time_slowdown_insight():
    engine = InsightEngine()
    result = engine.analyze(
        {"cycle_time": {"value": 8.4}},
        {"cycle_time": {"points": [{"value": 5.0}, {"value": 8.4}]}},
    )

    assert any(item["id"] == "cycle-time-slowdown" for item in result)


def test_bottleneck_insight_without_history():
    engine = InsightEngine()
    result = engine.analyze(
        {"wip": {"value": 12}, "throughput": {"value": 5}}
    )

    assert any(item["id"] == "wip-throughput-bottleneck" for item in result)


def test_planning_risk_insight():
    engine = InsightEngine()
    result = engine.analyze(
        {"commitment_vs_completed": {"value": 61.11}}
    )

    insight = next(item for item in result if item["id"] == "planning-risk")
    assert insight["severity"] == "medium"
    assert insight["metric"] == "commitment_vs_completed"


def test_no_insights_when_data_is_missing_or_healthy():
    engine = InsightEngine()
    result = engine.analyze(
        {"wip": {"value": 5}, "throughput": {"value": 5}, "commitment_vs_completed": {"value": 90}},
        {"wip": {"points": [{"value": 5}, {"value": 5}]}, "throughput": {"points": [{"value": 4}, {"value": 6}]}},
    )

    assert result == []


def test_flow_deterioration_insight():
    engine = InsightEngine()
    result = engine.analyze(
        {"wip": {"value": 12}, "cycle_time": {"value": 8.4}},
        {
            "wip": {"points": [{"value": 5}, {"value": 12}]},
            "cycle_time": {"points": [{"value": 4.0}, {"value": 8.4}]},
        },
    )
    insight = next(item for item in result if item["id"] == "flow-deterioration")
    assert insight["severity"] == "high"
    assert insight["confidence"] == "high"


def test_flow_deterioration_requires_both_trends():
    engine = InsightEngine()
    result = engine.analyze(
        {"wip": {"value": 12}, "cycle_time": {"value": 8.4}},
        {
            "wip": {"points": [{"value": 5}, {"value": 12}]},
            "cycle_time": {"points": [{"value": 8.4}, {"value": 8.4}]},
        },
    )
    assert not any(item["id"] == "flow-deterioration" for item in result)

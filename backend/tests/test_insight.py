from app.services.insight import InsightEngine


def test_wip_congestion_insight():
    result = InsightEngine().analyze(
        {"wip": {"value": 14}, "throughput": {"value": 5}},
        {
            "wip": {"points": [{"value": 8}, {"value": 14}]},
            "throughput": {"points": [{"value": 6}, {"value": 5}]},
        },
    )
    assert any(item["id"] == "wip-congestion" for item in result)


def test_throughput_decline_insight():
    result = InsightEngine().analyze(
        {"throughput": {"value": 5}},
        {"throughput": {"points": [{"value": 8}, {"value": 5}]}},
    )
    assert any(item["id"] == "throughput-decline" for item in result)


def test_cycle_time_slowdown_insight():
    result = InsightEngine().analyze(
        {"cycle_time": {"value": 8.4}},
        {"cycle_time": {"points": [{"value": 5.0}, {"value": 8.4}]}},
    )
    assert any(item["id"] == "cycle-time-slowdown" for item in result)


def test_lead_time_slowdown_insight():
    result = InsightEngine().analyze(
        {"lead_time": {"value": 10.0}},
        {"lead_time": {"points": [{"value": 6.0}, {"value": 10.0}]}},
    )
    assert any(item["id"] == "lead-time-slowdown" for item in result)


def test_velocity_decline_insight():
    result = InsightEngine().analyze(
        {"velocity": {"value": 18}},
        {"velocity": {"points": [{"value": 25}, {"value": 18}]}},
    )
    assert any(item["id"] == "velocity-decline" for item in result)


def test_planning_risk_insight():
    result = InsightEngine().analyze(
        {"commitment_vs_completed": {"value": 61.11}}
    )
    insight = next(item for item in result if item["id"] == "planning-risk")
    assert insight["severity"] == "medium"


def test_flow_deterioration_is_stronger_than_wip_congestion():
    result = InsightEngine().analyze(
        {"wip": {"value": 12}, "throughput": {"value": 5}, "cycle_time": {"value": 8.4}},
        {
            "wip": {"points": [{"value": 5}, {"value": 12}]},
            "throughput": {"points": [{"value": 6}, {"value": 5}]},
            "cycle_time": {"points": [{"value": 4.0}, {"value": 8.4}]},
        },
    )
    ids = {item["id"] for item in result}
    assert "flow-deterioration" in ids
    assert "wip-congestion" not in ids


def test_bottleneck_without_history():
    result = InsightEngine().analyze(
        {"wip": {"value": 12}, "throughput": {"value": 5}}
    )
    assert any(item["id"] == "wip-throughput-bottleneck" for item in result)


def test_healthy_metrics_produce_no_insights():
    result = InsightEngine().analyze(
        {
            "wip": {"value": 5},
            "throughput": {"value": 8},
            "cycle_time": {"value": 4},
            "lead_time": {"value": 6},
            "velocity": {"value": 25},
            "commitment_vs_completed": {"value": 90},
        },
        {
            "wip": {"points": [{"value": 6}, {"value": 5}]},
            "throughput": {"points": [{"value": 6}, {"value": 8}]},
            "cycle_time": {"points": [{"value": 5}, {"value": 4}]},
            "lead_time": {"points": [{"value": 8}, {"value": 6}]},
            "velocity": {"points": [{"value": 22}, {"value": 25}]},
        },
    )
    assert result == []

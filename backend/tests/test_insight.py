from app.services.insight import InsightEngine

def test_wip_congestion_contains_structured_evidence():
    result = InsightEngine().analyze(
        {"wip": {"value": 14}, "throughput": {"value": 5}},
        {
            "wip": {"points": [{"value": 8}, {"value": 14}]},
            "throughput": {"points": [{"value": 6}, {"value": 5}]},
        },
    )

    insight = next(
        item for item in result if item["id"] == "wip-congestion"
    )

    assert insight["evidence"]["wip"]["current"] == 14
    assert insight["evidence"]["wip"]["trend"] == 6
    assert insight["evidence"]["throughput"]["current"] == 5
    assert insight["evidence"]["throughput"]["trend"] == -1


def test_flow_deterioration_contains_structured_evidence():
    result = InsightEngine().analyze(
        {
            "wip": {"value": 12},
            "throughput": {"value": 5},
            "cycle_time": {"value": 8.4},
        },
        {
            "wip": {"points": [{"value": 5}, {"value": 12}]},
            "cycle_time": {"points": [{"value": 4.0}, {"value": 8.4}]},
        },
    )

    insight = next(
        item for item in result if item["id"] == "flow-deterioration"
    )

    assert insight["evidence"]["wip"]["current"] == 12
    assert insight["evidence"]["wip"]["trend"] == 7
    assert insight["evidence"]["cycle_time"]["current"] == 8.4
    assert insight["evidence"]["cycle_time"]["trend"] == 4.4
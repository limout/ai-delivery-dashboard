from app.metrics.registry import get_default_registry

def test_default_registry_contains_throughput():
    registry = get_default_registry()

    metric = registry.get("throughput")

    assert metric.name == "throughput"
    assert metric.category == "flow"


def test_registry_lists_available_metrics():
    registry = get_default_registry()

    metrics = registry.list_metrics()
    metric_names = [metric.name for metric in metrics]

    assert len(metrics) == 6

    assert "throughput" in metric_names
    assert "cycle_time" in metric_names
    assert "lead_time" in metric_names
    assert "wip" in metric_names
    assert "velocity" in metric_names
    assert "commitment_vs_completed" in metric_names
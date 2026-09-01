from app.metrics.registry import get_default_registry


def test_default_registry_contains_throughput():
    registry = get_default_registry()

    metric = registry.get("throughput")

    assert metric.name == "throughput"
    assert metric.category == "flow"


def test_registry_lists_available_metrics():
    registry = get_default_registry()

    metrics = registry.list_metrics()

    assert len(metrics) == 1
    assert metrics[0].name == "throughput"
from app.metrics.base import Metric
from app.metrics.throughput import ThroughputMetric
from app.metrics.cycle_time import CycleTimeMetric

class MetricRegistry:
    def __init__(self):
        self._metrics: dict[str, Metric] = {}

    def register(self, metric: Metric):
        self._metrics[metric.name] = metric

    def get(self, name: str) -> Metric:
        if name not in self._metrics:
            raise KeyError(f"Unknown metric: {name}")

        return self._metrics[name]

    def list_metrics(self) -> list[Metric]:
        return list(self._metrics.values())


def get_default_registry() -> MetricRegistry:
    registry = MetricRegistry()

    registry.register(ThroughputMetric())
    registry.register(CycleTimeMetric())
    
    return registry
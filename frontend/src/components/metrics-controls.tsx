import { useDashboard } from "@/lib/dashboard-context";
import { formatMetricName, HISTORICAL_METRIC_NAMES } from "@/lib/format";

export function MetricsControls() {
  const {
    availableMetrics,
    selectedMetricNames,
    sourcesLoading,
    errorMessage,
    toggleMetric,
  } = useDashboard();

  const metricOrder = [...availableMetrics].sort((a, b) => {
    const order = HISTORICAL_METRIC_NAMES as readonly string[];
    const indexA = order.indexOf(a.name);
    const indexB = order.indexOf(b.name);
    return (indexA === -1 ? 999 : indexA) - (indexB === -1 ? 999 : indexB);
  });

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        {availableMetrics.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {sourcesLoading
              ? "Loading available metrics..."
              : "No metrics available."}
          </p>
        ) : (
          metricOrder.map((metric) => (
            <label
              key={metric.name}
              className="flex cursor-pointer items-center gap-1.5 text-sm"
            >
              <input
                type="checkbox"
                className="size-4 shrink-0 accent-foreground"
                checked={selectedMetricNames.includes(metric.name)}
                onChange={(event) =>
                  toggleMetric(metric.name, event.target.checked)
                }
              />
              {formatMetricName(metric.name)}
            </label>
          ))
        )}
      </div>

      {errorMessage ? (
        <p className="text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </section>
  );
}

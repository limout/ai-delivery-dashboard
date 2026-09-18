import { MetricCard } from "@/components/dashboard/metric-card";
import { isMetricUnavailable, unavailableReason } from "@/lib/delivery-briefing";
import { METRIC_CATEGORY_ORDER, formatMetricName } from "@/lib/format";
import type { MetricCatalogItem, MetricResult } from "@/types/api";

type MetricGridProps = {
  selectedMetricNames: string[];
  metrics: Record<string, MetricResult>;
  catalog: MetricCatalogItem[];
};

function categoryFor(
  name: string,
  metric: MetricResult,
  catalog: MetricCatalogItem[],
): string {
  return (
    metric.category ||
    catalog.find((item) => item.name === name)?.category ||
    "other"
  );
}

export function MetricGrid({
  selectedMetricNames,
  metrics,
  catalog,
}: MetricGridProps) {
  const entries = selectedMetricNames
    .filter((name) => name in metrics)
    .map((name) => ({
      name,
      metric: metrics[name],
      category: categoryFor(name, metrics[name], catalog),
    }));

  const measured = entries.filter((entry) => !isMetricUnavailable(entry.metric));
  const unavailable = entries.filter((entry) =>
    isMetricUnavailable(entry.metric),
  );

  const categories = [...new Set(measured.map((entry) => entry.category))].sort(
    (a, b) => {
      const indexA = METRIC_CATEGORY_ORDER.indexOf(
        a as (typeof METRIC_CATEGORY_ORDER)[number],
      );
      const indexB = METRIC_CATEGORY_ORDER.indexOf(
        b as (typeof METRIC_CATEGORY_ORDER)[number],
      );
      return (indexA === -1 ? 999 : indexA) - (indexB === -1 ? 999 : indexB);
    },
  );

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No current metrics are selected.
      </p>
    );
  }

  return (
    <div className="space-y-5">
      {categories.map((category) => (
        <section key={category} className="space-y-3">
          <h4 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            {category}
          </h4>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {measured
              .filter((entry) => entry.category === category)
              .map((entry) => (
                <MetricCard
                  key={entry.name}
                  name={entry.name}
                  metric={entry.metric}
                />
              ))}
          </div>
        </section>
      ))}

      {unavailable.length > 0 ? (
        <section className="space-y-2">
          <h4 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Not yet measurable
          </h4>
          <ul className="space-y-2 rounded-lg border border-dashed px-4 py-3">
            {unavailable.map((entry) => (
              <li key={entry.name} className="text-sm">
                <span className="font-medium">
                  {formatMetricName(entry.name)}
                </span>
                <span className="text-muted-foreground">
                  {` — ${unavailableReason(entry.metric)}`}
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

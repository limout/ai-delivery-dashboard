import { MetricCard } from "@/components/dashboard/metric-card";
import { METRIC_CATEGORY_ORDER } from "@/lib/format";
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

  const categories = [...new Set(entries.map((entry) => entry.category))].sort(
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
          <h3 className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            {category}
          </h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {entries
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
    </div>
  );
}

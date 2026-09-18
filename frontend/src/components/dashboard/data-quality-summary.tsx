import { getMetricQuality } from "@/lib/metric-quality";
import type { MetricResult } from "@/types/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type DataQualitySummaryProps = {
  metrics: Record<string, MetricResult> | null;
};

export function DataQualitySummary({ metrics }: DataQualitySummaryProps) {
  const loaded = Object.entries(metrics ?? {}).map(([name, metric]) => ({
    name,
    metric,
  }));

  const measured = loaded.filter((entry) => {
    const quality = getMetricQuality(entry.metric);
    return (
      entry.metric.value !== null &&
      quality?.rawStatus !== "insufficient_data"
    );
  });
  const missingCount = loaded.length - measured.length;

  return (
    <Card className="rounded-lg shadow-none">
      <CardHeader>
        <CardTitle className="text-base">Data quality</CardTitle>
        <CardDescription>
          Completeness of the evidence behind this briefing — not a delivery
          score.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {loaded.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No metric evidence was loaded.
          </p>
        ) : (
          <p className="text-sm">
            {measured.length} of {loaded.length} loaded{" "}
            {loaded.length === 1 ? "metric is" : "metrics are"} measurable.
          </p>
        )}
        {loaded.length > 0 && missingCount === 0 ? (
          <p className="text-sm text-muted-foreground">
            All loaded metrics have enough data to measure.
          </p>
        ) : loaded.length > 0 ? (
          <p className="text-sm text-muted-foreground">
            Remaining values are not yet measurable. Open Metrics for details.
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

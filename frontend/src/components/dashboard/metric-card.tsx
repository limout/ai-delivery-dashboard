import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DataQualityBadge } from "@/components/dashboard/data-quality";
import { formatMetricName } from "@/lib/format";
import { getMetricQuality } from "@/lib/metric-quality";
import type { MetricResult } from "@/types/api";

type MetricCardProps = {
  name: string;
  metric: MetricResult;
};

export function MetricCard({ name, metric }: MetricCardProps) {
  const quality = getMetricQuality(metric);
  const isEmpty = metric.value === null;
  const sampleSize = metric.sample_size;

  return (
    <Card className="gap-3 rounded-lg py-4 shadow-none">
      <CardHeader className="px-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardDescription className="text-[11px] tracking-wide uppercase">
              {formatMetricName(name)}
            </CardDescription>
            <CardTitle className="mt-2 text-3xl font-semibold tracking-tight">
              {isEmpty ? "N/A" : metric.value}
            </CardTitle>
          </div>
          {quality ? <DataQualityBadge quality={quality} /> : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-1 px-4 text-xs text-muted-foreground">
        <p>
          {isEmpty ? "No measurable value" : metric.unit}
        </p>
        {sampleSize === undefined ? null : (
          <p>Sample: {sampleSize}</p>
        )}
        {quality?.message ? <p>{quality.message}</p> : null}
        {metric.description ? (
          <p className="pt-1 text-muted-foreground/90">{metric.description}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DataQualityBadge } from "@/components/dashboard/data-quality";
import { formatMetricName, isPlanningHistoryMetric } from "@/lib/format";
import { getMetricQuality } from "@/lib/metric-quality";
import { isMetricUnavailable, unavailableReason } from "@/lib/delivery-briefing";
import type { MetricResult } from "@/types/api";

type MetricCardProps = {
  name: string;
  metric: MetricResult;
};

export function MetricCard({ name, metric }: MetricCardProps) {
  const quality = getMetricQuality(metric);
  const unavailable = isMetricUnavailable(metric);
  const isZero = metric.value === 0;
  const showSufficient = quality?.message && quality.message !== "Sufficient data available.";

  return (
    <Card className="gap-3 rounded-lg py-4 shadow-none">
      <CardHeader className="px-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardDescription className="text-[11px] tracking-wide uppercase">
              {formatMetricName(name)}
            </CardDescription>
            <CardTitle
              className={
                unavailable
                  ? "mt-2 text-lg font-semibold tracking-tight"
                  : "mt-2 text-3xl font-semibold tracking-tight"
              }
            >
              {unavailable ? "Not available" : metric.value}
            </CardTitle>
          </div>
          {quality && !unavailable ? (
            <DataQualityBadge quality={quality} />
          ) : null}
        </div>
      </CardHeader>
      <CardContent className="space-y-1 px-4 text-xs text-muted-foreground">
        {unavailable ? (
          <p>{unavailableReason(metric)}</p>
        ) : (
          <>
            <p>
              {isZero
                ? `0 ${metric.unit} — a measured zero, not missing data.`
                : metric.unit}
            </p>
            {name === "commitment_vs_completed" ? (
              <p>
                Proxy of currently assigned story points completed — not
                sprint-start commitment.
              </p>
            ) : null}
            {isPlanningHistoryMetric(name) ? (
              <p>Measured by iteration, not by 7/14/30-day windows.</p>
            ) : null}
            {showSufficient ? <p>{quality?.message}</p> : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

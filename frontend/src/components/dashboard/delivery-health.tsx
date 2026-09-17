import { DataQualityBadge } from "@/components/dashboard/data-quality";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getMetricQuality } from "@/lib/metric-quality";
import type { MetricResult } from "@/types/api";

type DeliveryHealthProps = {
  metrics: Record<string, MetricResult> | null;
};

export function DeliveryHealth({ metrics }: DeliveryHealthProps) {
  const qualities = Object.values(metrics ?? {})
    .map((metric) => getMetricQuality(metric))
    .filter((quality) => quality !== null);

  const goodCount = qualities.filter(
    (quality) => quality.rawStatus === "good" || quality.rawStatus === "ok",
  ).length;
  const insufficientCount = qualities.filter(
    (quality) => quality.rawStatus === "insufficient_data",
  ).length;

  return (
    <Card className="rounded-lg shadow-none">
      <CardHeader>
        <CardTitle className="text-base">Delivery health</CardTitle>
        <CardDescription>
          Quality of the currently loaded metrics.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {qualities.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {goodCount > 0 ? (
              <DataQualityBadge
                quality={{
                  rawStatus: "good",
                  label: `${goodCount} good`,
                  semantic: "healthy",
                }}
              />
            ) : null}
            {insufficientCount > 0 ? (
              <DataQualityBadge
                quality={{
                  rawStatus: "insufficient_data",
                  label: `${insufficientCount} insufficient`,
                  semantic: "neutral",
                }}
              />
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No structured quality fields on the loaded metrics.
          </p>
        )}
        {insufficientCount > 0 ? (
          <p className="text-sm text-muted-foreground">
            {insufficientCount === 1
              ? "1 metric does not have enough history to measure."
              : `${insufficientCount} metrics do not have enough history to measure.`}
          </p>
        ) : null}
      </CardContent>
    </Card>
  );
}

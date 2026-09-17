import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  formatMetricName,
  HISTORICAL_METRIC_NAMES,
  isPlanningHistoryMetric,
} from "@/lib/format";
import type { HistoricalMetricsResponse } from "@/types/api";

type HistoryChartProps = {
  historical: HistoricalMetricsResponse | null;
  selectedMetric: string;
  selectedDays: number;
  selectedMetricNames: string[];
  isLoading: boolean;
  onSelectMetric: (metric: string) => void;
  onSelectDays: (days: number) => void;
};

function formatChartDate(dateString: string): string {
  const date = new Date(`${dateString}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return dateString;
  }
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function HistoryChart({
  historical,
  selectedMetric,
  selectedDays,
  selectedMetricNames,
  isLoading,
  onSelectMetric,
  onSelectDays,
}: HistoryChartProps) {
  const availableHistoryMetrics = HISTORICAL_METRIC_NAMES.filter((name) =>
    selectedMetricNames.includes(name),
  );
  const byIteration = isPlanningHistoryMetric(selectedMetric);
  const points = historical?.points ?? [];
  const numericPoints = points.filter(
    (point) => point.value !== null && Number.isFinite(point.value),
  );
  const chartData = points.map((point) => ({
    date: point.date,
    label: point.label ?? (point.date ? formatChartDate(point.date) : ""),
    value: point.value,
  }));

  return (
    <Card className="rounded-lg shadow-none">
      <CardHeader className="gap-4">
        <div>
          <CardTitle className="text-base">Historical Metrics</CardTitle>
          <CardDescription>
            {byIteration
              ? `${formatMetricName(selectedMetric)} by iteration.`
              : historical
                ? `${formatMetricName(historical.metric)}${historical.unit ? ` · ${historical.unit}` : ""}`
                : "Delivery metrics over the selected calendar window."}
          </CardDescription>
        </div>
        {availableHistoryMetrics.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {availableHistoryMetrics.map((metric) => (
              <Button
                key={metric}
                type="button"
                size="sm"
                variant={selectedMetric === metric ? "default" : "outline"}
                onClick={() => onSelectMetric(metric)}
              >
                {formatMetricName(metric)}
              </Button>
            ))}
          </div>
        ) : null}
        <div className="flex min-h-8 flex-wrap items-center gap-2">
          {byIteration ? (
            <p className="rounded-md border bg-muted/40 px-2.5 py-1.5 text-xs text-muted-foreground">
              Shown by iteration — calendar windows do not apply
            </p>
          ) : (
            <div className="flex gap-1">
              {[7, 14, 30].map((days) => (
                <Button
                  key={days}
                  type="button"
                  size="sm"
                  variant={selectedDays === days ? "default" : "outline"}
                  onClick={() => onSelectDays(days)}
                >
                  {days}d
                </Button>
              ))}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[280px] w-full" />
        ) : numericPoints.length === 0 ? (
          <div className="flex h-[280px] items-center justify-center rounded-md border border-dashed px-4 text-center text-sm text-muted-foreground">
            {byIteration
              ? "No iteration history is available for this metric."
              : "No measurable history for this metric in the selected window."}
          </div>
        ) : (
          <div className="h-[280px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                  tickLine={false}
                  axisLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                  tickLine={false}
                  axisLine={false}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid var(--border)",
                    background: "var(--card)",
                    fontSize: 12,
                  }}
                  formatter={(value) => [
                    value == null ? "N/A" : String(value),
                    historical?.unit ?? "value",
                  ]}
                  labelFormatter={(_, payload) => {
                    const row = payload?.[0]?.payload as
                      | { date?: string; label?: string }
                      | undefined;
                    if (!row) {
                      return "";
                    }
                    if (byIteration) {
                      return row.label ?? "";
                    }
                    return row.date ? formatChartDate(row.date) : (row.label ?? "");
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="var(--foreground)"
                  strokeWidth={2}
                  dot={byIteration}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

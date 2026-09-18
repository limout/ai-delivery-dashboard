import { HistoryChart } from "@/components/dashboard/history-chart";
import { MetricGrid } from "@/components/dashboard/metric-grid";
import { MetricsControls } from "@/components/metrics-controls";
import {
  PageEmpty,
  PageHeader,
  PageLoading,
  PageShell,
} from "@/components/page-header";
import { useDashboard } from "@/lib/dashboard-context";

export function MetricsPage() {
  const {
    projectLoaded,
    isLoadingDashboard,
    isHistoryLoading,
    historical,
    metrics,
    availableMetrics,
    selectedMetricNames,
    selectedHistoricalMetric,
    selectedHistoricalDays,
    selectHistoricalMetric,
    selectHistoricalDays,
  } = useDashboard();

  if (!projectLoaded && isLoadingDashboard) {
    return (
      <PageShell>
        <PageHeader
          title="Metrics"
          description="Choose which metrics to analyze, then inspect current values and history."
        />
        <MetricsControls />
        <PageLoading />
      </PageShell>
    );
  }

  if (!projectLoaded) {
    return (
      <PageEmpty title="Metrics">
        Select a source and project on Overview, then Load Dashboard to
        analyze metrics.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        title="Metrics"
        description="Choose which metrics to analyze, then inspect current values and history."
      />

      <MetricsControls />

      {isLoadingDashboard ? <PageLoading /> : null}

      <section className="space-y-3">
        <h3 className="text-sm font-semibold">Historical Metrics</h3>
        <HistoryChart
          historical={historical}
          selectedMetric={selectedHistoricalMetric}
          selectedDays={selectedHistoricalDays}
          selectedMetricNames={selectedMetricNames}
          isLoading={isHistoryLoading || isLoadingDashboard}
          onSelectMetric={selectHistoricalMetric}
          onSelectDays={selectHistoricalDays}
        />
      </section>

      <section className="space-y-3">
        <h3 className="text-sm font-semibold">KPI Details</h3>
        {metrics ? (
          <MetricGrid
            selectedMetricNames={selectedMetricNames}
            metrics={metrics}
            catalog={availableMetrics}
          />
        ) : (
          <p className="text-sm text-muted-foreground">
            Current metrics are not available.
          </p>
        )}
      </section>
    </PageShell>
  );
}

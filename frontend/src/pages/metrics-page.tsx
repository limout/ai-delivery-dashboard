import { HistoryChart } from "@/components/dashboard/history-chart";
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
    selectedMetricNames,
    selectedHistoricalMetric,
    selectedHistoricalDays,
    selectHistoricalMetric,
    selectHistoricalDays,
  } = useDashboard();

  if (isLoadingDashboard) {
    return (
      <PageShell>
        <PageHeader
          title="Metrics"
          description="Track delivery metrics over time."
        />
        <PageLoading />
      </PageShell>
    );
  }

  if (!projectLoaded) {
    return (
      <PageEmpty title="Metrics">
        Select a source and project on Overview, then load the dashboard to
        view historical metrics.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        title="Metrics"
        description="Track delivery metrics over time."
      />
      <HistoryChart
        historical={historical}
        selectedMetric={selectedHistoricalMetric}
        selectedDays={selectedHistoricalDays}
        selectedMetricNames={selectedMetricNames}
        isLoading={isHistoryLoading}
        onSelectMetric={selectHistoricalMetric}
        onSelectDays={selectHistoricalDays}
      />
    </PageShell>
  );
}

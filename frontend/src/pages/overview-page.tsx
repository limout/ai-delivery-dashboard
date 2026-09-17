import { DeliveryHealth } from "@/components/dashboard/delivery-health";
import { MetricGrid } from "@/components/dashboard/metric-grid";
import { WorkItemSummary } from "@/components/dashboard/work-item-summary";
import {
  PageEmpty,
  PageHeader,
  PageLoading,
  PageShell,
} from "@/components/page-header";
import { useDashboard } from "@/lib/dashboard-context";
import { formatSource } from "@/lib/format";

export function OverviewPage() {
  const {
    selectedProject,
    availableMetrics,
    selectedMetricNames,
    errorMessage,
    isLoadingDashboard,
    projectLoaded,
    loadedSource,
    loadedProject,
    workItems,
    metrics,
  } = useDashboard();

  const hasLoadError =
    Boolean(errorMessage) &&
    errorMessage.startsWith("Error loading metrics:") &&
    !projectLoaded;

  const kicker =
    loadedSource && loadedProject
      ? `${formatSource(loadedSource)} · ${loadedProject}`
      : null;

  if (isLoadingDashboard) {
    return (
      <PageShell>
        <PageLoading />
      </PageShell>
    );
  }

  if (!selectedProject && !projectLoaded) {
    return (
      <PageEmpty title="Overview">
        Select a source and project, then load the dashboard to see KPIs,
        delivery health, and work-item mix.
      </PageEmpty>
    );
  }

  if (selectedProject && !projectLoaded && !hasLoadError) {
    return (
      <PageEmpty title="Overview">
        {selectedProject} is selected. Load the dashboard to see current metrics
        and work items.
      </PageEmpty>
    );
  }

  if (hasLoadError) {
    return (
      <PageEmpty title="Overview">
        Dashboard data is unavailable. Resolve the issue in the controls above,
        then load again.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        kicker={kicker}
        title="Overview"
        description="Executive summary of the loaded project."
      />

      <section className="space-y-3">
        <h3 className="text-sm font-semibold">KPI summary</h3>
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

      <div className="grid gap-4 lg:grid-cols-2">
        <DeliveryHealth metrics={metrics} />
        <WorkItemSummary workItems={workItems} />
      </div>
    </PageShell>
  );
}

import type { ReactNode } from "react";

import { StatusBadge } from "@/components/status-badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useDashboard } from "@/lib/dashboard-context";
import { formatMetricName, formatSource } from "@/lib/format";

type PlaceholderPageProps = {
  title: string;
  description: string;
  children?: ReactNode;
};

export function PlaceholderPage({
  title,
  description,
  children,
}: PlaceholderPageProps) {
  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          {description}
        </p>
      </div>
      {children}
    </div>
  );
}

export function OverviewPage() {
  const {
    projectLoaded,
    loadedSource,
    loadedProject,
    workItems,
    metrics,
    historical,
    isLoadingDashboard,
  } = useDashboard();

  const metricCount = metrics ? Object.keys(metrics).length : 0;

  return (
    <PlaceholderPage
      title="Overview"
      description="Source, project, and Load are wired to the existing FastAPI endpoints. Detailed KPI, table, chart, Insights, and AI views remain for later phases."
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="gap-3 py-4 shadow-none">
          <CardHeader className="px-4">
            <CardDescription>Source</CardDescription>
            <CardTitle className="text-base font-medium">
              {loadedSource ? formatSource(loadedSource) : "Not selected"}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card className="gap-3 py-4 shadow-none">
          <CardHeader className="px-4">
            <CardDescription>Project</CardDescription>
            <CardTitle className="text-base font-medium">
              {loadedProject || "Not selected"}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card className="gap-3 py-4 shadow-none">
          <CardHeader className="px-4">
            <CardDescription>Work items</CardDescription>
            <CardTitle className="text-base font-medium">
              {isLoadingDashboard
                ? "Loading…"
                : projectLoaded || workItems.length
                  ? `${workItems.length} loaded`
                  : "Not loaded"}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card className="gap-3 py-4 shadow-none">
          <CardHeader className="px-4">
            <CardDescription>Dashboard data</CardDescription>
            <CardTitle>
              <StatusBadge
                status={
                  projectLoaded ? "healthy" : workItems.length ? "warning" : "neutral"
                }
              >
                {projectLoaded
                  ? "Ready"
                  : workItems.length
                    ? "Partial"
                    : "Awaiting load"}
              </StatusBadge>
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Loaded payload</CardTitle>
          <CardDescription>
            {projectLoaded
              ? `${metricCount} current metric${metricCount === 1 ? "" : "s"} and ${historical ? `history for ${formatMetricName(historical.metric)}` : "no history series"} are in memory.`
              : "Choose a connected source, a project key, at least one metric, then click Load. Insights and AI are not requested in this phase."}
          </CardDescription>
        </CardHeader>
      </Card>
    </PlaceholderPage>
  );
}

export function MetricsPage() {
  const { metrics, historical, projectLoaded, isLoadingDashboard } =
    useDashboard();

  const entries = metrics ? Object.entries(metrics) : [];

  return (
    <PlaceholderPage
      title="Metrics"
      description="Current metric values are stored after Load. Full KPI cards and Recharts history come later."
    >
      {isLoadingDashboard ? (
        <p className="text-sm text-muted-foreground">Loading metrics…</p>
      ) : null}

      {!projectLoaded && !isLoadingDashboard ? (
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>No metrics loaded</CardTitle>
            <CardDescription>
              Load a project from the controls above. Checkbox changes after a
              successful load refetch the same pipeline.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {entries.length > 0 ? (
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>Current values</CardTitle>
            <CardDescription>
              {historical
                ? `History loaded for ${formatMetricName(historical.metric)} (${historical.points?.length ?? 0} points).`
                : "No historical series in memory."}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            {entries.map(([name, metric]) => (
              <div
                key={name}
                className="flex items-baseline justify-between gap-4 border-b py-2 text-sm last:border-0"
              >
                <span>{formatMetricName(name)}</span>
                <span className="text-muted-foreground">
                  {metric.value === null ? "N/A" : String(metric.value)}
                  {metric.value === null ? "" : ` ${metric.unit}`}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </PlaceholderPage>
  );
}

export function WorkItemsPage() {
  const { workItems, projectLoaded, loadedProject, isLoadingDashboard } =
    useDashboard();

  return (
    <PlaceholderPage
      title="Work Items"
      description="Work items are fetched on Load and kept in state. The full table UI is not in this phase."
    >
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Normalized work items</CardTitle>
          <CardDescription>
            {isLoadingDashboard
              ? "Loading work items…"
              : projectLoaded || workItems.length
                ? `${workItems.length} item${workItems.length === 1 ? "" : "s"} loaded for ${loadedProject}.`
                : "Load a dashboard to fetch work items. The table is not rendered yet."}
          </CardDescription>
        </CardHeader>
      </Card>
    </PlaceholderPage>
  );
}

export function InsightsPage() {
  const { projectLoaded } = useDashboard();

  return (
    <PlaceholderPage
      title="Insights"
      description="Insights are not fetched in this phase. After Load, the vanilla app only reveals the panel; GET /insights stays on-demand later."
    >
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Delivery insights</CardTitle>
          <CardDescription>
            {projectLoaded
              ? "Dashboard data is loaded. Insight requests are intentionally not sent yet."
              : "Load a project first. This page will not call the insights API in Phase 2."}
          </CardDescription>
        </CardHeader>
      </Card>
    </PlaceholderPage>
  );
}

export function AIAnalysisPage() {
  const { projectLoaded } = useDashboard();

  return (
    <PlaceholderPage
      title="AI Analysis"
      description="AI analyze is not called in this phase, matching the vanilla Load path."
    >
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Evidence-based analysis</CardTitle>
          <CardDescription>
            {projectLoaded
              ? "Ready to analyze in a later phase. GET /ai/analyze is not invoked here."
              : "Load a project first. This page will not call the AI API in Phase 2."}
          </CardDescription>
        </CardHeader>
      </Card>
    </PlaceholderPage>
  );
}

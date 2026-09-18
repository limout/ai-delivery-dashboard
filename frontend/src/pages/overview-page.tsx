import { DeliveryRisk } from "@/components/dashboard/delivery-risk";
import { DataQualitySummary } from "@/components/dashboard/data-quality-summary";
import { ExecutiveBriefing } from "@/components/dashboard/executive-briefing";
import { WorkItemSummary } from "@/components/dashboard/work-item-summary";
import {
  PageEmpty,
  PageHeader,
  PageLoading,
  PageShell,
} from "@/components/page-header";
import { buildDeliveryBriefing } from "@/lib/delivery-briefing";
import { useDashboard } from "@/lib/dashboard-context";
import { formatSource } from "@/lib/format";
import { useMemo } from "react";

function formatLoadedAt(loadedAt: number | null): string | null {
  if (!loadedAt) {
    return null;
  }
  return new Date(loadedAt).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function OverviewPage() {
  const {
    selectedProject,
    errorMessage,
    isLoadingDashboard,
    projectLoaded,
    loadedSource,
    loadedProject,
    loadedAt,
    workItems,
    metrics,
    historical,
  } = useDashboard();

  const hasLoadError =
    Boolean(errorMessage) &&
    errorMessage.startsWith("Error loading metrics:") &&
    !projectLoaded;

  const kicker =
    loadedSource && loadedProject
      ? `${formatSource(loadedSource)} · ${loadedProject}`
      : null;

  const asOf = formatLoadedAt(loadedAt);
  const briefing = useMemo(
    () => buildDeliveryBriefing(metrics, workItems, historical),
    [historical, metrics, workItems],
  );

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
        Select a source and project, then Load Dashboard to see a delivery
        briefing for that project.
      </PageEmpty>
    );
  }

  if (selectedProject && !projectLoaded && !hasLoadError) {
    return (
      <PageEmpty title="Overview">
        {selectedProject} is selected. Load Dashboard to see the delivery
        briefing.
      </PageEmpty>
    );
  }

  if (hasLoadError) {
    return (
      <PageEmpty title="Overview">
        Delivery data could not be loaded. Resolve the issue in the controls
        above, then Load Dashboard again.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        kicker={kicker}
        title="Overview"
        description={
          asOf
            ? `As of ${asOf}`
            : "Delivery briefing for the loaded project."
        }
      />

      <ExecutiveBriefing briefing={briefing} />

      <DeliveryRisk
        concerns={briefing.concerns}
        dataInsufficient={briefing.dataInsufficient}
      />

      <WorkItemSummary workItems={workItems} />

      <DataQualitySummary metrics={metrics} />
    </PageShell>
  );
}

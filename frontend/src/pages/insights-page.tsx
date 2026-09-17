import { Loader2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { InsightCard } from "@/components/insights/insight-card";
import {
  PageEmpty,
  PageHeader,
  PageMessage,
  PageShell,
} from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/api/client";
import { useDashboard } from "@/lib/dashboard-context";
import { formatSource } from "@/lib/format";
import { countBySeverity, formatInsightLabel } from "@/lib/insights";
import { userFacingError } from "@/lib/user-facing-error";
import type { InsightsResponse } from "@/types/api";

const INSIGHTS_DAYS = 14;

const inflight = new Map<string, Promise<InsightsResponse>>();

function fetchInsights(project: string, source: string) {
  const key = `${source}::${project}::${INSIGHTS_DAYS}`;
  const existing = inflight.get(key);
  if (existing) {
    return existing;
  }
  const request = api
    .getInsights(project, source, INSIGHTS_DAYS)
    .finally(() => {
      inflight.delete(key);
    });
  inflight.set(key, request);
  return request;
}

type InsightsState = {
  loading: boolean;
  result: InsightsResponse | null;
  error: string | null | undefined;
};

const idleState: InsightsState = {
  loading: false,
  result: null,
  error: undefined,
};

export function InsightsPage() {
  const {
    projectLoaded,
    loadedSource,
    loadedProject,
    isLoadingDashboard,
  } = useDashboard();

  const [state, setState] = useState<InsightsState>(idleState);
  const requestIdRef = useRef(0);

  const canFetch =
    projectLoaded &&
    Boolean(loadedProject) &&
    Boolean(loadedSource) &&
    !isLoadingDashboard;

  useEffect(() => {
    if (!projectLoaded) {
      requestIdRef.current += 1;
      setState(idleState);
      return;
    }

    if (!canFetch) {
      return;
    }

    const requestId = ++requestIdRef.current;
    const project = loadedProject;
    const source = loadedSource;
    setState({ loading: true, result: null, error: undefined });

    void (async () => {
      try {
        const result = await fetchInsights(project, source);
        if (requestId !== requestIdRef.current) {
          return;
        }
        setState({ loading: false, result, error: null });
      } catch (error) {
        if (requestId !== requestIdRef.current) {
          return;
        }
        setState({
          loading: false,
          result: null,
          error: userFacingError(error),
        });
      }
    })();
  }, [canFetch, loadedProject, loadedSource, projectLoaded]);

  const insights = state.result?.insights ?? [];
  const severityCounts = useMemo(
    () => countBySeverity(insights.map((insight) => insight.severity)),
    [insights],
  );

  const kicker =
    loadedSource && loadedProject
      ? `${formatSource(loadedSource)} · ${loadedProject}`
      : null;

  if (!projectLoaded) {
    return (
      <PageEmpty title="Delivery Insights">
        Select a source and project on Overview, then load the dashboard to
        view delivery insights.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        kicker={kicker}
        title="Delivery Insights"
        description="Delivery signals identified from the loaded project data."
      />

      {state.loading || isLoadingDashboard ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Reviewing delivery data…
          </div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : null}

      {state.error !== undefined &&
      !state.loading &&
      !isLoadingDashboard &&
      !state.result ? (
        <PageMessage>
          Delivery insights could not be loaded.
          {state.error ? ` ${state.error}` : ""}
        </PageMessage>
      ) : null}

      {!state.loading && !isLoadingDashboard && state.result ? (
        insights.length === 0 ? (
          <PageMessage>
            No delivery insights were identified for the selected project.
          </PageMessage>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm text-muted-foreground">
                {insights.length} delivery{" "}
                {insights.length === 1 ? "insight" : "insights"}
              </p>
              {severityCounts.map((entry) => (
                <StatusBadge key={entry.severity} status={entry.severity}>
                  {entry.count}{" "}
                  {formatInsightLabel(entry.severity) ?? entry.severity}
                </StatusBadge>
              ))}
            </div>
            <div className="flex flex-col gap-4">
              {insights.map((insight) => (
                <InsightCard
                  key={insight.id || insight.title}
                  insight={insight}
                />
              ))}
            </div>
          </div>
        )
      ) : null}
    </PageShell>
  );
}

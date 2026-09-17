import { Loader2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { AnalysisSection } from "@/components/ai-analysis/analysis-section";
import {
  PageEmpty,
  PageHeader,
  PageMessage,
  PageShell,
} from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/api/client";
import { toTextItems } from "@/lib/ai-analysis";
import { useDashboard } from "@/lib/dashboard-context";
import { formatInsightLabel } from "@/lib/insights";
import { formatSource } from "@/lib/format";
import { userFacingError } from "@/lib/user-facing-error";
import type { AIAnalyzeResponse } from "@/types/api";

const ANALYSIS_DAYS = 14;

const inflight = new Map<string, Promise<AIAnalyzeResponse>>();

function fetchAnalysis(project: string, source: string) {
  const key = `${source}::${project}::${ANALYSIS_DAYS}`;
  const existing = inflight.get(key);
  if (existing) {
    return existing;
  }
  const request = api
    .getAIAnalysis(project, source, ANALYSIS_DAYS)
    .finally(() => {
      inflight.delete(key);
    });
  inflight.set(key, request);
  return request;
}

type AnalysisState = {
  loading: boolean;
  result: AIAnalyzeResponse | null;
  error: string | null | undefined;
};

const idleState: AnalysisState = {
  loading: false,
  result: null,
  error: undefined,
};

export function AIAnalysisPage() {
  const {
    projectLoaded,
    loadedSource,
    loadedProject,
    isLoadingDashboard,
  } = useDashboard();

  const [state, setState] = useState<AnalysisState>(idleState);
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
        const result = await fetchAnalysis(project, source);
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

  const analysis = state.result?.analysis;
  const facts = useMemo(() => toTextItems(analysis?.facts), [analysis]);
  const interpretation = useMemo(
    () => toTextItems(analysis?.interpretation),
    [analysis],
  );
  const impact = useMemo(() => toTextItems(analysis?.impact), [analysis]);
  const investigate = useMemo(
    () => toTextItems(analysis?.investigate),
    [analysis],
  );
  const recommendations = useMemo(
    () => toTextItems(analysis?.recommendations),
    [analysis],
  );
  const dataGaps = useMemo(() => toTextItems(analysis?.data_gaps), [analysis]);

  const riskTitle = analysis?.risk?.title?.trim() || null;
  const riskSeverity = analysis?.risk?.severity?.trim() || null;
  const hasContent =
    Boolean(riskTitle || riskSeverity) ||
    facts.length > 0 ||
    interpretation.length > 0 ||
    impact.length > 0 ||
    investigate.length > 0 ||
    recommendations.length > 0 ||
    dataGaps.length > 0;

  const kicker =
    loadedSource && loadedProject
      ? `${formatSource(loadedSource)} · ${loadedProject}`
      : null;

  if (!projectLoaded) {
    return (
      <PageEmpty title="AI Delivery Intelligence">
        Select a source and project on Overview, then load the dashboard to
        view AI delivery analysis.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        kicker={kicker}
        title="AI Delivery Intelligence"
        description="Evidence-based analysis of the loaded delivery data."
      />

      {state.loading || isLoadingDashboard ? (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            Analyzing delivery data…
          </div>
          <Skeleton className="h-24 w-full" />
          <div className="grid gap-4 lg:grid-cols-2">
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
          <Skeleton className="h-32 w-full" />
        </div>
      ) : null}

      {state.error !== undefined &&
      !state.loading &&
      !isLoadingDashboard &&
      !state.result ? (
        <PageMessage>
          AI analysis could not be generated.
          {state.error ? ` ${state.error}` : ""}
        </PageMessage>
      ) : null}

      {!state.loading &&
      !isLoadingDashboard &&
      state.result &&
      !hasContent ? (
        <PageMessage>
          No AI analysis was returned for the selected project.
        </PageMessage>
      ) : null}

      {!state.loading && !isLoadingDashboard && state.result && hasContent ? (
        <div className="flex flex-col gap-4">
          {riskTitle || riskSeverity ? (
            <Card className="rounded-lg py-5 shadow-none">
              <CardHeader className="px-5">
                <CardTitle className="text-base">Risk</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2 px-5 sm:flex-row sm:items-start sm:gap-3">
                {riskSeverity ? (
                  <StatusBadge status={riskSeverity}>
                    {formatInsightLabel(riskSeverity) ?? riskSeverity}
                  </StatusBadge>
                ) : null}
                {riskTitle ? (
                  <p className="text-base font-medium leading-snug break-words">
                    {riskTitle}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          {facts.length > 0 || interpretation.length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <AnalysisSection title="Facts" items={facts} />
              <AnalysisSection
                title="Interpretation"
                items={interpretation}
                asParagraphs
              />
            </div>
          ) : null}

          <AnalysisSection title="Impact" items={impact} asParagraphs />
          <AnalysisSection title="What to investigate" items={investigate} />
          <AnalysisSection title="Recommendations" items={recommendations} />
          <AnalysisSection title="Data gaps" items={dataGaps} />
        </div>
      ) : null}
    </PageShell>
  );
}

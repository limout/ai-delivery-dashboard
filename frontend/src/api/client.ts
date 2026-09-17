import type {
  AIAnalyzeResponse,
  HistoricalMetricsResponse,
  InsightsResponse,
  MetricsCatalogResponse,
  ProjectMetricsResponse,
  SourceProjectsResponse,
  SourcesResponse,
  WorkItemsResponse,
} from "@/types/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function queryString(
  params: Record<string, string | number | Array<string | number> | undefined>,
): string {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) {
      continue;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        search.append(key, String(item));
      }
      continue;
    }

    search.set(key, String(value));
  }

  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        message = payload.detail;
      }
    } catch {
      // Keep the generic HTTP error when the body is not JSON.
    }
    throw new ApiError(response.status, message);
  }

  return (await response.json()) as T;
}

export const api = {
  getMetricsCatalog: () => getJson<MetricsCatalogResponse>("/metrics"),

  getSources: () => getJson<SourcesResponse>("/sources"),

  getSourceProjects: (source: string) =>
    getJson<SourceProjectsResponse>(
      `/sources/${encodeURIComponent(source)}/projects`,
    ),

  getWorkItems: (project: string, source: string) =>
    getJson<WorkItemsResponse>(
      `/projects/${encodeURIComponent(project)}/work-items${queryString({ source })}`,
    ),

  getProjectMetrics: (
    project: string,
    source: string,
    metricNames: string[],
  ) =>
    getJson<ProjectMetricsResponse>(
      `/projects/${encodeURIComponent(project)}/metrics${queryString({
        source,
        metric_names: metricNames,
      })}`,
    ),

  getMetricsHistory: (
    project: string,
    source: string,
    metric: string,
    days: number,
  ) =>
    getJson<HistoricalMetricsResponse>(
      `/projects/${encodeURIComponent(project)}/metrics/history${queryString({
        source,
        metric,
        days,
      })}`,
    ),

  getInsights: (project: string, source: string, days = 14) =>
    getJson<InsightsResponse>(
      `/projects/${encodeURIComponent(project)}/insights${queryString({
        source,
        days,
      })}`,
    ),

  getAIAnalysis: (project: string, source: string, days = 14) =>
    getJson<AIAnalyzeResponse>(
      `/projects/${encodeURIComponent(project)}/ai/analyze${queryString({
        source,
        days,
      })}`,
    ),
};

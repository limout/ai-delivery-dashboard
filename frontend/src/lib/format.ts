export function formatSource(source: string): string {
  return source === "azure_devops" ? "Azure DevOps" : "Jira";
}

export function formatMetricName(name: string): string {
  return name.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export const METRIC_CATEGORY_ORDER = [
  "snapshot",
  "flow",
  "planning",
  "business",
  "team",
  "other",
] as const;

export const HISTORICAL_METRIC_NAMES = [
  "wip",
  "throughput",
  "cycle_time",
  "lead_time",
  "velocity",
  "commitment_vs_completed",
] as const;

export const PLANNING_HISTORY_METRICS = [
  "velocity",
  "commitment_vs_completed",
] as const;

export type HistoricalMetricName = (typeof HISTORICAL_METRIC_NAMES)[number];

export function isPlanningHistoryMetric(metric: string): boolean {
  return PLANNING_HISTORY_METRICS.includes(
    metric as (typeof PLANNING_HISTORY_METRICS)[number],
  );
}

export function formatRole(role: string | undefined): string {
  if (!role) {
    return "Unknown";
  }
  return role.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatQualityStatus(status: string): string {
  return status.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function sortMetricCategories(categories: string[]): string[] {
  return [...categories].sort((a, b) => {
    const indexA = METRIC_CATEGORY_ORDER.indexOf(
      a as (typeof METRIC_CATEGORY_ORDER)[number],
    );
    const indexB = METRIC_CATEGORY_ORDER.indexOf(
      b as (typeof METRIC_CATEGORY_ORDER)[number],
    );
    return (indexA === -1 ? 999 : indexA) - (indexB === -1 ? 999 : indexB);
  });
}

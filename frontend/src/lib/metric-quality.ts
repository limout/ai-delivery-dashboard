import { resolveSemanticStatus, type SemanticStatus } from "@/lib/status";
import { formatQualityStatus } from "@/lib/format";
import type { MetricResult } from "@/types/api";

export type MetricQuality = {
  rawStatus: string;
  label: string;
  message?: string;
  semantic: SemanticStatus;
};

export function getMetricQuality(metric: MetricResult): MetricQuality | null {
  if (metric.data_quality?.status) {
    return {
      rawStatus: metric.data_quality.status,
      label: formatQualityStatus(metric.data_quality.status),
      message: metric.data_quality.message,
      semantic: resolveSemanticStatus(metric.data_quality.status),
    };
  }

  if (metric.status) {
    return {
      rawStatus: metric.status,
      label: formatQualityStatus(metric.status),
      message: metric.message,
      semantic: resolveSemanticStatus(metric.status),
    };
  }

  return null;
}

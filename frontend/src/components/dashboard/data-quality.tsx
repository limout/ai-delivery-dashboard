import { StatusBadge } from "@/components/status-badge";
import { cn } from "@/lib/utils";
import type { MetricQuality } from "@/lib/metric-quality";

type DataQualityBadgeProps = {
  quality: MetricQuality;
  className?: string;
};

export function DataQualityBadge({ quality, className }: DataQualityBadgeProps) {
  return (
    <StatusBadge status={quality.semantic} className={cn("font-medium", className)}>
      {quality.label}
    </StatusBadge>
  );
}

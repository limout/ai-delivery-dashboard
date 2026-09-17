import { InsightEvidence } from "@/components/insights/insight-evidence";
import { StatusBadge } from "@/components/status-badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatMetricName } from "@/lib/format";
import {
  displayInsightText,
  formatInsightLabel,
} from "@/lib/insights";
import type { Insight } from "@/types/api";

type InsightCardProps = {
  insight: Insight;
};

function Block({ label, value }: { label: string; value?: string | null }) {
  const text = displayInsightText(value);
  if (!text) {
    return null;
  }
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {label}
      </p>
      <p className="text-sm leading-relaxed break-words">{text}</p>
    </div>
  );
}

export function InsightCard({ insight }: InsightCardProps) {
  const severityLabel = formatInsightLabel(insight.severity) ?? "Unknown";
  const title = displayInsightText(insight.title) ?? "Delivery insight";
  const confidence = formatInsightLabel(insight.confidence);
  const metric = displayInsightText(insight.metric)
    ? formatMetricName(insight.metric)
    : null;
  const evidence = insight.evidence;

  return (
    <Card className="rounded-lg py-5 shadow-none">
      <CardHeader className="gap-3 px-5">
        <div className="flex flex-wrap items-start gap-2">
          <StatusBadge status={insight.severity}>{severityLabel}</StatusBadge>
          <CardTitle className="min-w-0 text-base leading-snug break-words">
            {title}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 px-5">
        <Block label="Fact" value={insight.fact} />
        <Block label="Signal" value={insight.signal} />
        <Block label="Recommendation" value={insight.recommendation} />

        {metric || confidence ? (
          <p className="text-xs text-muted-foreground">
            {metric ? `Metric: ${metric}` : null}
            {metric && confidence ? " · " : null}
            {confidence ? `Confidence: ${confidence}` : null}
          </p>
        ) : null}

        {evidence ? (
          <InsightEvidence
            wipCount={evidence.wip_count}
            blockedCount={evidence.blocked_count}
            wipItems={evidence.wip_items}
            blockedItems={evidence.blocked_items}
          />
        ) : null}
      </CardContent>
    </Card>
  );
}

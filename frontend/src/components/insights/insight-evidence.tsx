import type { InsightEvidenceItem } from "@/types/api";

function text(value: string | number | null | undefined): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string" && value.trim() === "") {
    return null;
  }
  return String(value);
}

function EvidenceItemRow({ item }: { item: InsightEvidenceItem }) {
  const title = text(item.title);
  const id = text(item.id);
  const status = text(item.status);
  const assignee = text(item.assignee) ?? "Unassigned";
  const priority = text(item.priority);
  const age =
    item.age_days === null || item.age_days === undefined
      ? null
      : `${item.age_days} days`;

  return (
    <li className="rounded-md border border-border/70 px-3 py-2">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="min-w-0 text-sm">
          {id ? (
            <span className="mr-2 font-mono text-xs text-muted-foreground">
              {id}
            </span>
          ) : null}
          <span className="break-words">{title ?? "—"}</span>
        </p>
        {age ? (
          <span className="shrink-0 text-xs text-muted-foreground">{age}</span>
        ) : null}
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {[status, assignee, priority].filter(Boolean).join(" · ")}
      </p>
    </li>
  );
}

type InsightEvidenceProps = {
  wipCount?: number;
  blockedCount?: number;
  wipItems?: InsightEvidenceItem[];
  blockedItems?: InsightEvidenceItem[];
};

export function InsightEvidence({
  wipCount,
  blockedCount,
  wipItems,
  blockedItems,
}: InsightEvidenceProps) {
  const wip = wipItems ?? [];
  const blocked = blockedItems ?? [];
  const hasCounts = wipCount !== undefined || blockedCount !== undefined;
  const hasItems = wip.length > 0 || blocked.length > 0;

  if (!hasCounts && !hasItems) {
    return null;
  }

  return (
    <div className="space-y-3">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        Evidence
      </p>
      {hasCounts ? (
        <p className="text-xs text-muted-foreground">
          {wipCount !== undefined
            ? `Showing ${wip.length} of ${wipCount} in-progress items`
            : null}
          {wipCount !== undefined && blockedCount !== undefined ? " · " : null}
          {blockedCount !== undefined ? `${blockedCount} blocked` : null}
        </p>
      ) : null}

      {wip.length > 0 ? (
        <ul className="space-y-2">
          {wip.map((item) => (
            <EvidenceItemRow key={item.id || item.title} item={item} />
          ))}
        </ul>
      ) : null}

      {blocked.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            Blocked items: {blocked.length}
          </p>
          <ul className="space-y-2">
            {blocked.map((item) => (
              <EvidenceItemRow
                key={`blocked-${item.id || item.title}`}
                item={item}
              />
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

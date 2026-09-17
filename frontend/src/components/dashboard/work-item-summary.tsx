import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatRole } from "@/lib/format";
import type { WorkItem } from "@/types/api";

type WorkItemSummaryProps = {
  workItems: WorkItem[];
};

function counts(items: string[]): { label: string; count: number }[] {
  const tally = new Map<string, number>();
  for (const item of items) {
    tally.set(item, (tally.get(item) ?? 0) + 1);
  }
  return [...tally.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

function Distribution({
  title,
  rows,
  total,
}: {
  title: string;
  rows: { label: string; count: number }[];
  total: number;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
        {title}
      </p>
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">None</p>
      ) : (
        <ul className="space-y-2">
          {rows.slice(0, 6).map((row) => (
            <li key={row.label} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="truncate pr-2">{row.label}</span>
                <span className="text-muted-foreground">{row.count}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-foreground/70"
                  style={{ width: `${total ? (row.count / total) * 100 : 0}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function WorkItemSummary({ workItems }: WorkItemSummaryProps) {
  const statuses = counts(
    workItems.map((item) => item.status || "Unknown"),
  );
  const roles = counts(
    workItems.map((item) => formatRole(String(item.delivery_role))),
  );

  return (
    <Card className="rounded-lg shadow-none">
      <CardHeader>
        <CardTitle className="text-base">Work item mix</CardTitle>
        <CardDescription>
          {workItems.length} work {workItems.length === 1 ? "item" : "items"} from
          the loaded project.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6 sm:grid-cols-2">
        <Distribution title="Status" rows={statuses} total={workItems.length} />
        <Distribution title="Role" rows={roles} total={workItems.length} />
      </CardContent>
    </Card>
  );
}

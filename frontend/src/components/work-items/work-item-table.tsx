import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  displayAssignee,
  displayValue,
  workItemRoleLabel,
  type WorkItemSort,
  type WorkItemSortKey,
} from "@/lib/work-items";
import type { WorkItem } from "@/types/api";

type WorkItemTableProps = {
  items: WorkItem[];
  sort: WorkItemSort;
  onSort: (key: WorkItemSortKey) => void;
};

const columns: {
  key: WorkItemSortKey | "id" | "type" | "role";
  label: string;
  sortable?: boolean;
  className?: string;
  hideClass?: string;
}[] = [
  { key: "id", label: "ID", className: "w-[7.5rem]", hideClass: "hidden sm:table-cell" },
  { key: "type", label: "Type", hideClass: "hidden sm:table-cell" },
  { key: "title", label: "Title", sortable: true, className: "min-w-[12rem]" },
  { key: "status", label: "Status", sortable: true },
  { key: "priority", label: "Priority", sortable: true, hideClass: "hidden md:table-cell" },
  { key: "assignee", label: "Assignee", sortable: true, hideClass: "hidden md:table-cell" },
  { key: "iteration", label: "Iteration", sortable: true, hideClass: "hidden lg:table-cell" },
  {
    key: "story_points",
    label: "Story Points",
    sortable: true,
    hideClass: "hidden lg:table-cell",
    className: "text-right",
  },
  { key: "role", label: "Role", hideClass: "hidden md:table-cell" },
];

function SortIcon({
  active,
  direction,
}: {
  active: boolean;
  direction: "asc" | "desc";
}) {
  if (!active) {
    return <ArrowUpDown className="size-3 text-muted-foreground/70" />;
  }
  return direction === "asc" ? (
    <ArrowUp className="size-3" />
  ) : (
    <ArrowDown className="size-3" />
  );
}

export function WorkItemTable({ items, sort, onSort }: WorkItemTableProps) {
  return (
    <div className="min-w-0 overflow-x-auto rounded-lg border bg-card">
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-card">
          <tr className="border-b text-left text-xs font-medium tracking-wide text-muted-foreground uppercase">
            {columns.map((column) => {
              const sortable = Boolean(column.sortable);
              const active = sortable && sort.key === column.key;
              return (
                <th
                  key={column.key}
                  className={cn(
                    "whitespace-nowrap px-3 py-2 font-medium",
                    column.className,
                    column.hideClass,
                  )}
                >
                  {sortable ? (
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 hover:text-foreground"
                      onClick={() => onSort(column.key as WorkItemSortKey)}
                    >
                      {column.label}
                      <SortIcon
                        active={active}
                        direction={sort.direction}
                      />
                    </button>
                  ) : (
                    column.label
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.source}-${item.id}`}
              className="border-b last:border-b-0 hover:bg-muted/40"
            >
              <td
                className={cn(
                  "px-3 py-2 font-mono text-xs text-muted-foreground",
                  "hidden sm:table-cell",
                )}
              >
                {displayValue(item.id)}
              </td>
              <td className="hidden px-3 py-2 whitespace-nowrap sm:table-cell">
                {displayValue(item.type)}
              </td>
              <td className="max-w-[20rem] px-3 py-2">
                <span className="line-clamp-2" title={item.title || undefined}>
                  {displayValue(item.title)}
                </span>
                <span className="mt-0.5 block font-mono text-[11px] text-muted-foreground sm:hidden">
                  {displayValue(item.id)}
                </span>
              </td>
              <td className="px-3 py-2">
                {item.status ? (
                  <Badge variant="outline">{item.status}</Badge>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="hidden px-3 py-2 md:table-cell">
                {item.priority ? (
                  <Badge variant="secondary">{item.priority}</Badge>
                ) : (
                  <span className="text-muted-foreground">—</span>
                )}
              </td>
              <td className="hidden max-w-[10rem] truncate px-3 py-2 md:table-cell">
                {displayAssignee(item.assignee)}
              </td>
              <td className="hidden max-w-[10rem] truncate px-3 py-2 lg:table-cell">
                {displayValue(item.iteration)}
              </td>
              <td className="hidden px-3 py-2 text-right tabular-nums lg:table-cell">
                {displayValue(item.story_points)}
              </td>
              <td className="hidden px-3 py-2 md:table-cell">
                <Badge variant="outline">{workItemRoleLabel(item)}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

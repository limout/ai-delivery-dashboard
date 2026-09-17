import { formatRole } from "@/lib/format";
import type { WorkItem } from "@/types/api";

export const FILTER_ALL = "__all__";
export const FILTER_EMPTY = "__empty__";

export type WorkItemSortKey =
  | "title"
  | "status"
  | "priority"
  | "assignee"
  | "iteration"
  | "story_points";

export type WorkItemSort = {
  key: WorkItemSortKey;
  direction: "asc" | "desc";
};

export type WorkItemFilters = {
  status: string;
  type: string;
  priority: string;
  role: string;
  assignee: string;
};

export const EMPTY_FILTERS: WorkItemFilters = {
  status: FILTER_ALL,
  type: FILTER_ALL,
  priority: FILTER_ALL,
  role: FILTER_ALL,
  assignee: FILTER_ALL,
};

export function displayValue(
  value: string | number | null | undefined,
): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "string" && value.trim() === "") {
    return "—";
  }
  return String(value);
}

export function displayAssignee(value: string | null | undefined): string {
  if (value === null || value === undefined || value.trim() === "") {
    return "Unassigned";
  }
  return value;
}

function fieldKey(value: string | null | undefined): string {
  if (value === null || value === undefined || value.trim() === "") {
    return FILTER_EMPTY;
  }
  return value;
}

export function uniqueOptions(
  items: WorkItem[],
  getter: (item: WorkItem) => string | null | undefined,
  format: (value: string) => string = (value) => value,
): { value: string; label: string }[] {
  const seen = new Map<string, string>();
  for (const item of items) {
    const raw = fieldKey(getter(item));
    if (!seen.has(raw)) {
      seen.set(raw, raw === FILTER_EMPTY ? "—" : format(raw));
    }
  }
  return [...seen.entries()]
    .sort((a, b) => {
      if (a[0] === FILTER_EMPTY) {
        return 1;
      }
      if (b[0] === FILTER_EMPTY) {
        return -1;
      }
      return a[1].localeCompare(b[1], undefined, { sensitivity: "base" });
    })
    .map(([value, label]) => ({ value, label }));
}

export function matchesSearch(item: WorkItem, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return true;
  }
  return [item.id, item.title, item.assignee, item.iteration].some(
    (value) => value != null && String(value).toLowerCase().includes(needle),
  );
}

export function matchesFilters(
  item: WorkItem,
  filters: WorkItemFilters,
): boolean {
  if (filters.status !== FILTER_ALL && fieldKey(item.status) !== filters.status) {
    return false;
  }
  if (filters.type !== FILTER_ALL && fieldKey(item.type) !== filters.type) {
    return false;
  }
  if (
    filters.priority !== FILTER_ALL &&
    fieldKey(item.priority) !== filters.priority
  ) {
    return false;
  }
  if (filters.role !== FILTER_ALL && fieldKey(String(item.delivery_role)) !== filters.role) {
    return false;
  }
  if (
    filters.assignee !== FILTER_ALL &&
    fieldKey(item.assignee) !== filters.assignee
  ) {
    return false;
  }
  return true;
}

function sortValue(
  item: WorkItem,
  key: WorkItemSortKey,
): string | number | null {
  switch (key) {
    case "title":
      return item.title || null;
    case "status":
      return item.status;
    case "priority":
      return item.priority;
    case "assignee":
      return item.assignee;
    case "iteration":
      return item.iteration;
    case "story_points":
      return item.story_points;
  }
}

export function sortWorkItems(
  items: WorkItem[],
  sort: WorkItemSort,
): WorkItem[] {
  const multiplier = sort.direction === "asc" ? 1 : -1;
  return [...items].sort((left, right) => {
    const a = sortValue(left, sort.key);
    const b = sortValue(right, sort.key);
    if (a == null && b == null) {
      return left.id.localeCompare(right.id);
    }
    if (a == null) {
      return 1;
    }
    if (b == null) {
      return -1;
    }
    if (typeof a === "number" && typeof b === "number") {
      return (a - b) * multiplier || left.id.localeCompare(right.id);
    }
    return (
      String(a).localeCompare(String(b), undefined, {
        numeric: true,
        sensitivity: "base",
      }) * multiplier || left.id.localeCompare(right.id)
    );
  });
}

export function filterAndSortWorkItems(
  items: WorkItem[],
  query: string,
  filters: WorkItemFilters,
  sort: WorkItemSort,
): WorkItem[] {
  const filtered = items.filter(
    (item) => matchesSearch(item, query) && matchesFilters(item, filters),
  );
  return sortWorkItems(filtered, sort);
}

export function hasActiveFilters(
  query: string,
  filters: WorkItemFilters,
): boolean {
  return (
    query.trim() !== "" ||
    Object.values(filters).some((value) => value !== FILTER_ALL)
  );
}

export function workItemRoleLabel(item: WorkItem): string {
  return formatRole(String(item.delivery_role));
}

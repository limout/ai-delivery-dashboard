import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatRole } from "@/lib/format";
import {
  FILTER_ALL,
  FILTER_EMPTY,
  uniqueOptions,
  type WorkItemFilters,
} from "@/lib/work-items";
import type { WorkItem } from "@/types/api";

type WorkItemToolbarProps = {
  items: WorkItem[];
  query: string;
  filters: WorkItemFilters;
  resultCount: number;
  totalCount: number;
  onQueryChange: (value: string) => void;
  onFiltersChange: (filters: WorkItemFilters) => void;
  onClear: () => void;
  canClear: boolean;
};

function FilterSelect({
  id,
  label,
  value,
  options,
  allLabel,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: { value: string; label: string }[];
  allLabel: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="grid min-w-[140px] flex-1 gap-1.5">
      <label htmlFor={id} className="text-xs font-medium text-muted-foreground">
        {label}
      </label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id} size="sm" className="w-full">
          <SelectValue placeholder={allLabel} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={FILTER_ALL}>{allLabel}</SelectItem>
          {options.map((option) => (
            <SelectItem key={`${id}-${option.value}`} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export function WorkItemToolbar({
  items,
  query,
  filters,
  resultCount,
  totalCount,
  onQueryChange,
  onFiltersChange,
  onClear,
  canClear,
}: WorkItemToolbarProps) {
  const statusOptions = uniqueOptions(items, (item) => item.status);
  const typeOptions = uniqueOptions(items, (item) => item.type);
  const priorityOptions = uniqueOptions(items, (item) => item.priority);
  const roleOptions = uniqueOptions(
    items,
    (item) => String(item.delivery_role ?? ""),
    formatRole,
  );
  const assigneeOptions = uniqueOptions(items, (item) => item.assignee).map(
    (option) =>
      option.value === FILTER_EMPTY
        ? { ...option, label: "Unassigned" }
        : option,
  );

  return (
    <div className="space-y-3">
      <Input
        type="search"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        placeholder="Search work items"
        aria-label="Search work items"
        className="max-w-md"
      />

      <div className="flex flex-col gap-3 lg:flex-row lg:flex-wrap lg:items-end">
        <FilterSelect
          id="filter-status"
          label="Status"
          value={filters.status}
          options={statusOptions}
          allLabel="All statuses"
          onChange={(value) => onFiltersChange({ ...filters, status: value })}
        />
        <FilterSelect
          id="filter-type"
          label="Type"
          value={filters.type}
          options={typeOptions}
          allLabel="All types"
          onChange={(value) => onFiltersChange({ ...filters, type: value })}
        />
        <FilterSelect
          id="filter-priority"
          label="Priority"
          value={filters.priority}
          options={priorityOptions}
          allLabel="All priorities"
          onChange={(value) => onFiltersChange({ ...filters, priority: value })}
        />
        <FilterSelect
          id="filter-role"
          label="Role"
          value={filters.role}
          options={roleOptions}
          allLabel="All roles"
          onChange={(value) => onFiltersChange({ ...filters, role: value })}
        />
        <FilterSelect
          id="filter-assignee"
          label="Assignee"
          value={filters.assignee}
          options={assigneeOptions}
          allLabel="All assignees"
          onChange={(value) => onFiltersChange({ ...filters, assignee: value })}
        />
        {canClear ? (
          <Button type="button" variant="ghost" size="sm" onClick={onClear}>
            Clear
          </Button>
        ) : null}
      </div>

      <p className="text-xs text-muted-foreground">
        Showing {resultCount} of {totalCount} work{" "}
        {totalCount === 1 ? "item" : "items"}
      </p>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";

import { WorkItemTable } from "@/components/work-items/work-item-table";
import { WorkItemToolbar } from "@/components/work-items/work-item-toolbar";
import {
  PageEmpty,
  PageHeader,
  PageLoading,
  PageMessage,
  PageShell,
} from "@/components/page-header";
import { useDashboard } from "@/lib/dashboard-context";
import { formatSource } from "@/lib/format";
import {
  EMPTY_FILTERS,
  filterAndSortWorkItems,
  hasActiveFilters,
  type WorkItemFilters,
  type WorkItemSort,
  type WorkItemSortKey,
} from "@/lib/work-items";

export function WorkItemsPage() {
  const {
    selectedProject,
    errorMessage,
    isLoadingDashboard,
    projectLoaded,
    loadedSource,
    loadedProject,
    workItems,
  } = useDashboard();

  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<WorkItemFilters>(EMPTY_FILTERS);
  const [sort, setSort] = useState<WorkItemSort>({
    key: "title",
    direction: "asc",
  });

  useEffect(() => {
    setQuery("");
    setFilters(EMPTY_FILTERS);
    setSort({ key: "title", direction: "asc" });
  }, [loadedSource, loadedProject]);

  const visibleItems = useMemo(
    () => filterAndSortWorkItems(workItems, query, filters, sort),
    [workItems, query, filters, sort],
  );

  const canClear = hasActiveFilters(query, filters);

  const hasLoadError =
    Boolean(errorMessage) &&
    errorMessage.startsWith("Error loading metrics:") &&
    !projectLoaded;

  const kicker =
    loadedSource && loadedProject
      ? `${formatSource(loadedSource)} · ${loadedProject}`
      : null;

  function handleSort(key: WorkItemSortKey) {
    setSort((current) =>
      current.key === key
        ? { key, direction: current.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" },
    );
  }

  if (isLoadingDashboard) {
    return (
      <PageShell>
        <PageHeader title="Work Items" />
        <PageLoading />
      </PageShell>
    );
  }

  if (!selectedProject && !projectLoaded) {
    return (
      <PageEmpty title="Work Items">
        Select a source and project on Overview, then load the dashboard to see
        work items.
      </PageEmpty>
    );
  }

  if (selectedProject && !projectLoaded && !hasLoadError) {
    return (
      <PageEmpty title="Work Items">
        {selectedProject} is selected. Load the dashboard from Overview to fetch
        work items.
      </PageEmpty>
    );
  }

  if (hasLoadError) {
    return (
      <PageEmpty title="Work Items">
        Work item data is unavailable. Resolve the issue on Overview, then load
        again.
      </PageEmpty>
    );
  }

  return (
    <PageShell>
      <PageHeader
        kicker={kicker}
        title="Work Items"
        description={`${workItems.length} work ${workItems.length === 1 ? "item" : "items"}`}
      />

      {workItems.length === 0 ? (
        <PageMessage>No work items were returned for this project.</PageMessage>
      ) : (
        <>
          <WorkItemToolbar
            items={workItems}
            query={query}
            filters={filters}
            resultCount={visibleItems.length}
            totalCount={workItems.length}
            onQueryChange={setQuery}
            onFiltersChange={setFilters}
            onClear={() => {
              setQuery("");
              setFilters(EMPTY_FILTERS);
            }}
            canClear={canClear}
          />

          {visibleItems.length === 0 ? (
            <PageMessage>
              No work items match the current search and filters.
            </PageMessage>
          ) : (
            <WorkItemTable
              items={visibleItems}
              sort={sort}
              onSort={handleSort}
            />
          )}
        </>
      )}
    </PageShell>
  );
}

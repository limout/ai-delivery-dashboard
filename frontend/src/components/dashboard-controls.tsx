import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDashboard } from "@/lib/dashboard-context";
import {
  formatMetricName,
  sortMetricCategories,
} from "@/lib/format";

const EMPTY_SOURCE = "__empty_source__";
const EMPTY_PROJECT = "__empty_project__";

export function DashboardControls() {
  const {
    sources,
    sourcesLoading,
    selectedSource,
    projects,
    projectsLoading,
    projectsError,
    selectedProject,
    availableMetrics,
    selectedMetricNames,
    selectionStatus,
    errorMessage,
    loadButtonLabel,
    isLoadingDashboard,
    selectSource,
    selectProject,
    toggleMetric,
    loadDashboard,
  } = useDashboard();

  const categories = sortMetricCategories([
    ...new Set(availableMetrics.map((metric) => metric.category || "other")),
  ]);

  const canLoad =
    Boolean(selectedProject) &&
    !isLoadingDashboard &&
    !projectsLoading;

  return (
    <section className="border-b bg-card px-4 py-3 md:px-8">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end gap-3">
          <div className="grid min-w-[160px] flex-1 gap-1 sm:max-w-[240px]">
            <label htmlFor="source-select" className="text-sm font-medium">
              Source
            </label>
            <Select
              value={selectedSource || EMPTY_SOURCE}
              onValueChange={(value) =>
                selectSource(value === EMPTY_SOURCE ? "" : value)
              }
              disabled={sourcesLoading}
            >
              <SelectTrigger id="source-select" className="w-[240px] max-w-full">
                <SelectValue
                  placeholder={
                    sourcesLoading ? "Loading sources..." : "Select a source..."
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={EMPTY_SOURCE}>
                  {sourcesLoading ? "Loading sources..." : "Select a source..."}
                </SelectItem>
                {sources.map((source) => (
                  <SelectItem
                    key={source.source}
                    value={source.source}
                    disabled={source.status !== "connected"}
                  >
                    {source.label}
                    {source.status !== "connected" ? " (unavailable)" : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid min-w-[160px] flex-1 gap-1 sm:max-w-[280px]">
            <label htmlFor="project-select" className="text-sm font-medium">
              Project
            </label>
            <Select
              value={selectedProject || EMPTY_PROJECT}
              onValueChange={(value) =>
                selectProject(value === EMPTY_PROJECT ? "" : value)
              }
              disabled={!selectedSource || projectsLoading || projectsError}
            >
              <SelectTrigger id="project-select" className="w-[280px] max-w-full">
                <SelectValue
                  placeholder={
                    projectsLoading
                      ? "Loading projects..."
                      : "Select a project..."
                  }
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={EMPTY_PROJECT}>
                  {projectsLoading
                    ? "Loading projects..."
                    : "Select a project..."}
                </SelectItem>
                {projects.map((project) => (
                  <SelectItem key={project.key} value={project.key}>
                    {project.name} ({project.key})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            type="button"
            size="sm"
            disabled={!canLoad}
            onClick={() => void loadDashboard()}
          >
            <RefreshCw className="size-3.5" />
            {loadButtonLabel}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">{selectionStatus}</p>

        <div>
          <h2 className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Metrics included in Load
          </h2>
          {availableMetrics.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {sourcesLoading
                ? "Loading available metrics..."
                : "No metrics available."}
            </p>
          ) : (
            <div className="flex flex-col gap-2.5">
              {categories.map((category) => (
                <div key={category}>
                  <p className="mb-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                    {category}
                  </p>
                  <div className="flex flex-wrap gap-x-4 gap-y-2">
                    {availableMetrics
                      .filter(
                        (metric) => (metric.category || "other") === category,
                      )
                      .map((metric) => (
                        <label
                          key={metric.name}
                          className="flex cursor-pointer items-center gap-2 text-sm"
                        >
                          <input
                            type="checkbox"
                            className="size-4 accent-foreground"
                            checked={selectedMetricNames.includes(metric.name)}
                            onChange={(event) =>
                              toggleMetric(metric.name, event.target.checked)
                            }
                          />
                          {formatMetricName(metric.name)}
                        </label>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {errorMessage ? (
          <p className="text-sm text-destructive" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </div>
    </section>
  );
}

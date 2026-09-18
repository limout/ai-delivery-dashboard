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
    selectionStatus,
    errorMessage,
    loadButtonLabel,
    isLoadingDashboard,
    selectSource,
    selectProject,
    loadDashboard,
  } = useDashboard();

  const canLoad =
    Boolean(selectedProject) && !isLoadingDashboard && !projectsLoading;

  return (
    <section className="border-b bg-card px-4 py-3 md:px-8">
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="grid w-full min-w-0 gap-1 sm:max-w-[240px] sm:flex-1">
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
              <SelectTrigger id="source-select" className="w-full">
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

          <div className="grid w-full min-w-0 gap-1 sm:max-w-[280px] sm:flex-1">
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
              <SelectTrigger id="project-select" className="w-full">
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
            className="w-fit shrink-0"
            disabled={!canLoad}
            onClick={() => void loadDashboard()}
          >
            <RefreshCw className="size-3.5" />
            {loadButtonLabel}
          </Button>
        </div>

        <p className="text-xs text-muted-foreground">{selectionStatus}</p>

        {errorMessage ? (
          <p className="text-sm text-destructive" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </div>
    </section>
  );
}

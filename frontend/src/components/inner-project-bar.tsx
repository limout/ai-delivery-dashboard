import { useDashboard } from "@/lib/dashboard-context";
import { formatSource } from "@/lib/format";

export function InnerProjectBar() {
  const {
    projectLoaded,
    loadedSource,
    loadedProject,
    selectedSource,
    selectedProject,
    errorMessage,
    isLoadingDashboard,
  } = useDashboard();

  const source = loadedSource || selectedSource;
  const project = loadedProject || selectedProject;

  return (
    <section className="border-b bg-card px-4 py-2.5 md:px-8">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <p className="min-w-0 text-sm break-words">
          {source && project ? (
            <>
              <span className="font-medium">
                {formatSource(source)} · {project}
              </span>
              <span className="text-muted-foreground">
                {projectLoaded
                  ? " · Loaded"
                  : " · Load the dashboard from Overview"}
              </span>
            </>
          ) : (
            <span className="text-muted-foreground">
              Select a source and project on Overview, then load.
            </span>
          )}
        </p>
        {isLoadingDashboard ? (
          <span className="text-xs text-muted-foreground">Loading…</span>
        ) : null}
      </div>
      {errorMessage ? (
        <p className="mt-1.5 text-sm text-destructive" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </section>
  );
}

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/api/client";
import {
  formatSource,
  HISTORICAL_METRIC_NAMES,
} from "@/lib/format";
import type {
  HistoricalMetricsResponse,
  MetricCatalogItem,
  ProjectMetricsResponse,
  ProjectSummary,
  SourceConnection,
  WorkItem,
} from "@/types/api";

type LoadButtonLabel = "Load Dashboard" | "Loading..." | "Load Metrics";

type DashboardContextValue = {
  sources: SourceConnection[];
  sourcesLoading: boolean;
  selectedSource: string;
  projects: ProjectSummary[];
  projectsLoading: boolean;
  projectsError: boolean;
  selectedProject: string;
  availableMetrics: MetricCatalogItem[];
  selectedMetricNames: string[];
  selectionStatus: string;
  errorMessage: string;
  loadButtonLabel: LoadButtonLabel;
  isLoadingDashboard: boolean;
  projectLoaded: boolean;
  loadedSource: string;
  loadedProject: string;
  workItems: WorkItem[];
  metrics: ProjectMetricsResponse | null;
  historical: HistoricalMetricsResponse | null;
  selectSource: (source: string) => void;
  selectProject: (projectKey: string) => void;
  toggleMetric: (metricName: string, checked: boolean) => void;
  loadDashboard: () => Promise<void>;
};

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [sources, setSources] = useState<SourceConnection[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState("");
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [projectsError, setProjectsError] = useState(false);
  const [selectedProject, setSelectedProject] = useState("");
  const [availableMetrics, setAvailableMetrics] = useState<MetricCatalogItem[]>(
    [],
  );
  const [selectedMetricNames, setSelectedMetricNames] = useState<string[]>([]);
  const [selectionStatus, setSelectionStatus] = useState(
    "Select a source and project to begin.",
  );
  const [errorMessage, setErrorMessage] = useState("");
  const [loadButtonLabel, setLoadButtonLabel] =
    useState<LoadButtonLabel>("Load Dashboard");
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(false);
  const [projectLoaded, setProjectLoaded] = useState(false);
  const [loadedSource, setLoadedSource] = useState("");
  const [loadedProject, setLoadedProject] = useState("");
  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [metrics, setMetrics] = useState<ProjectMetricsResponse | null>(null);
  const [historical, setHistorical] = useState<HistoricalMetricsResponse | null>(
    null,
  );

  const selectedMetricNamesRef = useRef(selectedMetricNames);
  selectedMetricNamesRef.current = selectedMetricNames;
  const selectedHistoricalMetricRef = useRef("wip");
  const projectRequestRef = useRef(0);
  const dashboardRequestRef = useRef(0);

  const clearLoadedDashboard = useCallback(() => {
    setProjectLoaded(false);
    setLoadedSource("");
    setLoadedProject("");
    setWorkItems([]);
    setMetrics(null);
    setHistorical(null);
    setErrorMessage("");
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function initializeDashboard() {
      try {
        const catalog = await api.getMetricsCatalog();
        if (cancelled) {
          return;
        }

        const metricsCatalog = catalog.available_metrics ?? [];
        setAvailableMetrics(metricsCatalog);
        setSelectedMetricNames(metricsCatalog.map((metric) => metric.name));
      } catch {
        if (!cancelled) {
          setErrorMessage(
            "Error initializing dashboard: Failed to load available metrics",
          );
          setSourcesLoading(false);
        }
        return;
      }

      try {
        const data = await api.getSources();
        if (cancelled) {
          return;
        }
        setSources(data.sources ?? []);
      } catch {
        if (!cancelled) {
          setSources([]);
          setErrorMessage("Failed to load sources");
        }
      } finally {
        if (!cancelled) {
          setSourcesLoading(false);
        }
      }
    }

    void initializeDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  const selectSource = useCallback(
    (source: string) => {
      dashboardRequestRef.current += 1;
      const requestId = ++projectRequestRef.current;

      setSelectedSource(source);
      setSelectedProject("");
      clearLoadedDashboard();

      if (!source) {
        setProjects([]);
        setProjectsLoading(false);
        setProjectsError(false);
        setSelectionStatus("Select a source and project to begin.");
        return;
      }

      setProjectsLoading(true);
      setProjectsError(false);
      setProjects([]);
      setSelectionStatus("Loading projects...");

      void (async () => {
        try {
          const data = await api.getSourceProjects(source);
          if (requestId !== projectRequestRef.current) {
            return;
          }
          const nextProjects = data.projects ?? [];
          setProjects(nextProjects);
          setProjectsError(false);
          setSelectionStatus(
            `${nextProjects.length} project${nextProjects.length === 1 ? "" : "s"} available in ${formatSource(source)}.`,
          );
        } catch {
          if (requestId !== projectRequestRef.current) {
            return;
          }
          setProjects([]);
          setProjectsError(true);
          setErrorMessage("Failed to load projects");
          setSelectionStatus("Unable to load projects");
        } finally {
          if (requestId === projectRequestRef.current) {
            setProjectsLoading(false);
          }
        }
      })();
    },
    [clearLoadedDashboard],
  );

  const selectProject = useCallback(
    (projectKey: string) => {
      dashboardRequestRef.current += 1;
      setSelectedProject(projectKey);
      clearLoadedDashboard();
      setSelectionStatus(
        projectKey
          ? `Ready to load ${formatSource(selectedSource)} · ${projectKey}.`
          : "Select a project to begin.",
      );
    },
    [clearLoadedDashboard, selectedSource],
  );

  const runLoad = useCallback(
    async (metricNames: string[]) => {
      const project = selectedProject.trim();
      const source = selectedSource;

      if (!project) {
        setErrorMessage("Error loading metrics: Project is required");
        return;
      }

      if (metricNames.length === 0) {
        setErrorMessage("Error loading metrics: Select at least one metric");
        return;
      }

      const requestId = ++dashboardRequestRef.current;
      setIsLoadingDashboard(true);
      setLoadButtonLabel("Loading...");
      setErrorMessage("");

      try {
        if (!source) {
          throw new Error("Failed to load work items");
        }

        let workData;
        try {
          workData = await api.getWorkItems(project, source);
        } catch {
          throw new Error("Failed to load work items");
        }
        if (requestId !== dashboardRequestRef.current) {
          return;
        }

        const items = workData.work_items ?? [];
        setWorkItems(items);
        setLoadedSource(source);
        setLoadedProject(project);

        let metricsData;
        try {
          metricsData = await api.getProjectMetrics(
            project,
            source,
            metricNames,
          );
        } catch {
          throw new Error("Failed to load metrics");
        }
        if (requestId !== dashboardRequestRef.current) {
          return;
        }

        const filteredMetrics: ProjectMetricsResponse = {};
        for (const [name, metric] of Object.entries(metricsData)) {
          if (metricNames.includes(name)) {
            filteredMetrics[name] = metric;
          }
        }
        setMetrics(filteredMetrics);
        setProjectLoaded(true);
        setSelectionStatus(
          `${items.length} normalized work items available`,
        );

        const historicalCandidates = HISTORICAL_METRIC_NAMES.filter((name) =>
          metricNames.includes(name),
        );

        if (historicalCandidates.length === 0) {
          setHistorical(null);
        } else {
          const preferred = selectedHistoricalMetricRef.current;
          const historyMetric = historicalCandidates.includes(
            preferred as (typeof HISTORICAL_METRIC_NAMES)[number],
          )
            ? preferred
            : historicalCandidates[0];
          selectedHistoricalMetricRef.current = historyMetric;

          try {
            const historyData = await api.getMetricsHistory(
              project,
              source,
              historyMetric,
              14,
            );
            if (requestId !== dashboardRequestRef.current) {
              return;
            }
            setHistorical(historyData);
          } catch {
            if (requestId !== dashboardRequestRef.current) {
              return;
            }
            setHistorical(null);
            setErrorMessage(
              "Error loading historical metrics: Failed to load historical metrics",
            );
          }
        }
      } catch (error) {
        if (requestId !== dashboardRequestRef.current) {
          return;
        }
        setMetrics(null);
        setHistorical(null);
        setProjectLoaded(false);
        const message =
          error instanceof Error ? error.message : "Failed to load metrics";
        setErrorMessage(`Error loading metrics: ${message}`);
      } finally {
        if (requestId === dashboardRequestRef.current) {
          setIsLoadingDashboard(false);
          setLoadButtonLabel("Load Metrics");
        }
      }
    },
    [selectedProject, selectedSource],
  );

  const loadDashboard = useCallback(async () => {
    await runLoad(selectedMetricNamesRef.current);
  }, [runLoad]);

  const toggleMetric = useCallback(
    (metricName: string, checked: boolean) => {
      const next = checked
        ? selectedMetricNames.includes(metricName)
          ? selectedMetricNames
          : [...selectedMetricNames, metricName]
        : selectedMetricNames.filter((name) => name !== metricName);

      setSelectedMetricNames(next);

      if (!projectLoaded) {
        return;
      }

      if (next.length === 0) {
        setMetrics(null);
        setHistorical(null);
        return;
      }

      void runLoad(next);
    },
    [projectLoaded, runLoad, selectedMetricNames],
  );

  const value = useMemo<DashboardContextValue>(
    () => ({
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
      projectLoaded,
      loadedSource,
      loadedProject,
      workItems,
      metrics,
      historical,
      selectSource,
      selectProject,
      toggleMetric,
      loadDashboard,
    }),
    [
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
      projectLoaded,
      loadedSource,
      loadedProject,
      workItems,
      metrics,
      historical,
      selectSource,
      selectProject,
      toggleMetric,
      loadDashboard,
    ],
  );

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboard must be used within DashboardProvider");
  }
  return context;
}

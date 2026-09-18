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
  type HistoricalMetricName,
} from "@/lib/format";
import type {
  HistoricalMetricsResponse,
  MetricCatalogItem,
  ProjectMetricsResponse,
  ProjectSummary,
  SourceConnection,
  WorkItem,
} from "@/types/api";

type LoadButtonLabel = "Load Dashboard" | "Loading…";

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
  isHistoryLoading: boolean;
  projectLoaded: boolean;
  loadedSource: string;
  loadedProject: string;
  loadedAt: number | null;
  workItems: WorkItem[];
  metrics: ProjectMetricsResponse | null;
  historical: HistoricalMetricsResponse | null;
  selectedHistoricalMetric: string;
  selectedHistoricalDays: number;
  selectSource: (source: string) => void;
  selectProject: (projectKey: string) => void;
  toggleMetric: (metricName: string, checked: boolean) => void;
  loadDashboard: () => Promise<void>;
  selectHistoricalMetric: (metric: string) => void;
  selectHistoricalDays: (days: number) => void;
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
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [projectLoaded, setProjectLoaded] = useState(false);
  const [loadedSource, setLoadedSource] = useState("");
  const [loadedProject, setLoadedProject] = useState("");
  const [loadedAt, setLoadedAt] = useState<number | null>(null);
  const [workItems, setWorkItems] = useState<WorkItem[]>([]);
  const [metrics, setMetrics] = useState<ProjectMetricsResponse | null>(null);
  const [historical, setHistorical] = useState<HistoricalMetricsResponse | null>(
    null,
  );
  const [selectedHistoricalMetric, setSelectedHistoricalMetric] = useState("wip");
  const [selectedHistoricalDays, setSelectedHistoricalDays] = useState(14);

  const selectedMetricNamesRef = useRef(selectedMetricNames);
  selectedMetricNamesRef.current = selectedMetricNames;
  const availableMetricsRef = useRef(availableMetrics);
  availableMetricsRef.current = availableMetrics;
  const selectedHistoricalMetricRef = useRef(selectedHistoricalMetric);
  selectedHistoricalMetricRef.current = selectedHistoricalMetric;
  const selectedHistoricalDaysRef = useRef(selectedHistoricalDays);
  selectedHistoricalDaysRef.current = selectedHistoricalDays;
  const loadedSourceRef = useRef(loadedSource);
  loadedSourceRef.current = loadedSource;
  const loadedProjectRef = useRef(loadedProject);
  loadedProjectRef.current = loadedProject;
  const projectRequestRef = useRef(0);
  const dashboardRequestRef = useRef(0);
  const historyRequestRef = useRef(0);

  const clearLoadedDashboard = useCallback(() => {
    dashboardRequestRef.current += 1;
    historyRequestRef.current += 1;
    setProjectLoaded(false);
    setLoadedSource("");
    setLoadedProject("");
    setLoadedAt(null);
    setWorkItems([]);
    setMetrics(null);
    setHistorical(null);
    setIsHistoryLoading(false);
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

  const resolveHistoryMetric = useCallback((metricNames: string[]) => {
    const candidates = HISTORICAL_METRIC_NAMES.filter((name) =>
      metricNames.includes(name),
    );
    if (candidates.length === 0) {
      return null;
    }
    const preferred = selectedHistoricalMetricRef.current;
    return candidates.includes(preferred as HistoricalMetricName)
      ? preferred
      : candidates[0];
  }, []);

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
      setLoadButtonLabel("Loading…");
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
        setLoadedAt(Date.now());
        setSelectionStatus(
          `${items.length} work ${items.length === 1 ? "item" : "items"} loaded.`,
        );

        const historyNames =
          selectedMetricNamesRef.current.length > 0
            ? selectedMetricNamesRef.current
            : metricNames;
        const historyMetric = resolveHistoryMetric(historyNames);
        if (!historyMetric) {
          setHistorical(null);
          return;
        }

        setSelectedHistoricalMetric(historyMetric);
        selectedHistoricalMetricRef.current = historyMetric;
        const days = selectedHistoricalDaysRef.current;
        const historyId = ++historyRequestRef.current;

        try {
          const historyData = await api.getMetricsHistory(
            project,
            source,
            historyMetric,
            days,
          );
          if (
            requestId !== dashboardRequestRef.current ||
            historyId !== historyRequestRef.current
          ) {
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
          setLoadButtonLabel("Load Dashboard");
        }
      }
    },
    [resolveHistoryMetric, selectedProject, selectedSource],
  );

  const catalogMetricNames = useCallback(() => {
    return availableMetricsRef.current.map((metric) => metric.name);
  }, []);

  const loadDashboard = useCallback(async () => {
    const names = catalogMetricNames();
    if (names.length === 0) {
      setErrorMessage("Error loading metrics: No metrics are available");
      return;
    }
    await runLoad(names);
  }, [catalogMetricNames, runLoad]);

  const fetchHistory = useCallback(async (metric: string, days: number) => {
    const source = loadedSourceRef.current;
    const project = loadedProjectRef.current;
    if (!source || !project) {
      return;
    }

    const requestId = ++historyRequestRef.current;
    setIsHistoryLoading(true);

    try {
      const historyData = await api.getMetricsHistory(
        project,
        source,
        metric,
        days,
      );
      if (requestId !== historyRequestRef.current) {
        return;
      }
      setHistorical(historyData);
    } catch {
      if (requestId !== historyRequestRef.current) {
        return;
      }
      setHistorical(null);
      setErrorMessage(
        "Error loading historical metrics: Failed to load historical metrics",
      );
    } finally {
      if (requestId === historyRequestRef.current) {
        setIsHistoryLoading(false);
      }
    }
  }, []);

  const toggleMetric = useCallback(
    (metricName: string, checked: boolean) => {
      const current = selectedMetricNamesRef.current;
      const next = checked
        ? current.includes(metricName)
          ? current
          : [...current, metricName]
        : current.filter((name) => name !== metricName);

      setSelectedMetricNames(next);

      if (
        next.length > 0 &&
        !next.includes(selectedHistoricalMetricRef.current)
      ) {
        const nextHistory = resolveHistoryMetric(next);
        if (nextHistory && projectLoaded) {
          setSelectedHistoricalMetric(nextHistory);
          selectedHistoricalMetricRef.current = nextHistory;
          void fetchHistory(nextHistory, selectedHistoricalDaysRef.current);
        }
      }
    },
    [fetchHistory, projectLoaded, resolveHistoryMetric],
  );

  const selectHistoricalMetric = useCallback(
    (metric: string) => {
      if (!selectedMetricNamesRef.current.includes(metric)) {
        return;
      }
      setSelectedHistoricalMetric(metric);
      selectedHistoricalMetricRef.current = metric;
      void fetchHistory(metric, selectedHistoricalDaysRef.current);
    },
    [fetchHistory],
  );

  const selectHistoricalDays = useCallback(
    (days: number) => {
      setSelectedHistoricalDays(days);
      selectedHistoricalDaysRef.current = days;
      void fetchHistory(selectedHistoricalMetricRef.current, days);
    },
    [fetchHistory],
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
      isHistoryLoading,
      projectLoaded,
      loadedSource,
      loadedProject,
      loadedAt,
      workItems,
      metrics,
      historical,
      selectedHistoricalMetric,
      selectedHistoricalDays,
      selectSource,
      selectProject,
      toggleMetric,
      loadDashboard,
      selectHistoricalMetric,
      selectHistoricalDays,
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
      isHistoryLoading,
      projectLoaded,
      loadedSource,
      loadedProject,
      loadedAt,
      workItems,
      metrics,
      historical,
      selectedHistoricalMetric,
      selectedHistoricalDays,
      selectSource,
      selectProject,
      toggleMetric,
      loadDashboard,
      selectHistoricalMetric,
      selectHistoricalDays,
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

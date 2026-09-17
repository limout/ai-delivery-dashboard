export type DeliverySourceName = "jira" | "azure_devops" | string;

export type SourceConnection = {
  source: string;
  label: string;
  status: "connected" | "error" | string;
  project_count: number;
  message?: string;
};

export type SourcesResponse = {
  sources: SourceConnection[];
};

export type ProjectSummary = {
  id: string;
  key: string;
  name: string;
};

export type SourceProjectsResponse = {
  source: string;
  projects: ProjectSummary[];
};

export type DeliveryRole =
  | "container"
  | "planning_item"
  | "execution_item"
  | "defect"
  | "unknown";

export type WorkItem = {
  id: string;
  source: string;
  project: string;
  type: string;
  title: string;
  status: string | null;
  priority: string | null;
  assignee: string | null;
  created_at: string | null;
  updated_at: string | null;
  due_date: string | null;
  iteration: string | null;
  parent_id: string | null;
  story_points: number | null;
  delivery_role: DeliveryRole | string;
};

export type WorkItemsResponse = {
  project: string;
  source: string;
  count: number;
  work_items: WorkItem[];
};

export type MetricCatalogItem = {
  name: string;
  description: string;
  category: string;
  required_data: string;
};

export type MetricsCatalogResponse = {
  available_metrics: MetricCatalogItem[];
};

export type DataQuality = {
  status: string;
  message: string;
};

export type MetricResult = {
  metric?: string;
  value: number | null;
  unit: string;
  sample_size?: number;
  data_quality?: DataQuality;
  description?: string;
  category?: string;
  status?: string;
  message?: string;
  iterations?: Record<string, unknown>;
};

export type ProjectMetricsResponse = Record<string, MetricResult>;

export type HistoricalPoint = {
  date: string;
  value: number | null;
  label?: string;
};

export type HistoricalMetricsResponse = {
  metric: string;
  unit?: string;
  status?: string;
  points: HistoricalPoint[];
};

export type InsightEvidenceItem = {
  id: string;
  title?: string;
  status?: string | null;
  assignee?: string | null;
  priority?: string | null;
  age_days?: number | null;
  source?: string;
};

export type Insight = {
  id: string;
  severity: string;
  title: string;
  fact: string;
  signal: string;
  recommendation: string;
  confidence: string;
  metric: string;
  evidence?: {
    evidence_type?: string;
    wip_count?: number;
    blocked_count?: number;
    wip_items?: InsightEvidenceItem[];
    blocked_items?: InsightEvidenceItem[];
  };
};

export type InsightsResponse = {
  project: string;
  days: number;
  source?: string;
  metrics: Record<string, MetricResult>;
  historical: Record<string, HistoricalMetricsResponse | unknown>;
  insights: Insight[];
};

export type AIRisk = {
  title: string;
  severity: "low" | "medium" | "high" | string;
};

export type AIAnalysisBody = {
  risk?: AIRisk | null;
  facts?: string[] | string;
  interpretation?: string[] | string;
  impact?: string[] | string;
  investigate?: string[] | string;
  recommendations?: string[] | string;
  data_gaps?: string[] | string;
};

export type AIAnalyzeResponse = {
  project: string;
  source: string;
  analysis_window_days: number;
  model?: string | null;
  analysis: AIAnalysisBody;
};

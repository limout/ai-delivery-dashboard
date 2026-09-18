import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/layouts/app-layout";
import { DashboardProvider } from "@/lib/dashboard-context";
import { AIAnalysisPage } from "@/pages/ai-analysis-page";
import { InsightsPage } from "@/pages/insights-page";
import { MetricsPage } from "@/pages/metrics-page";
import { OverviewPage } from "@/pages/overview-page";
import { WorkItemsPage } from "@/pages/work-items-page";

export default function App() {
  return (
    <DashboardProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="metrics" element={<MetricsPage />} />
            <Route path="work-items" element={<WorkItemsPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="ai-analysis" element={<AIAnalysisPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </DashboardProvider>
  );
}

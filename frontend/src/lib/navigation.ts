import {
  ChartLine,
  LayoutDashboard,
  ListTodo,
  Sparkles,
  TriangleAlert,
} from "lucide-react";

export const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/metrics", label: "Metrics", icon: ChartLine },
  { to: "/work-items", label: "Work Items", icon: ListTodo },
  { to: "/insights", label: "Insights", icon: TriangleAlert },
  { to: "/ai-analysis", label: "AI Analysis", icon: Sparkles },
] as const;

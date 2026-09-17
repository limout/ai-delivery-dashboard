import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { resolveSemanticStatus } from "@/lib/status";

const variantByStatus = {
  healthy: "healthy",
  info: "info",
  warning: "warning",
  critical: "critical",
  neutral: "neutral",
} as const;

type StatusBadgeProps = {
  status?: string;
  children: ReactNode;
  className?: string;
};

export function StatusBadge({ status, children, className }: StatusBadgeProps) {
  const semantic = resolveSemanticStatus(status);

  return (
    <Badge variant={variantByStatus[semantic]} className={className}>
      {children}
    </Badge>
  );
}

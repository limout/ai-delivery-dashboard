export const semanticStatus = {
  healthy: "healthy",
  good: "healthy",
  info: "info",
  medium: "warning",
  warning: "warning",
  high: "critical",
  critical: "critical",
  neutral: "neutral",
} as const;

export type SemanticStatus =
  (typeof semanticStatus)[keyof typeof semanticStatus];

export type StatusInput = keyof typeof semanticStatus;

export function resolveSemanticStatus(value: string | undefined): SemanticStatus {
  if (!value) {
    return "neutral";
  }

  const normalized = value.toLowerCase().trim();
  if (normalized in semanticStatus) {
    return semanticStatus[normalized as StatusInput];
  }

  return "neutral";
}

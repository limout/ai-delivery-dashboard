function hasText(value: unknown): value is string {
  return typeof value === "string" && value.trim() !== "";
}

export function displayInsightText(value: string | null | undefined): string | null {
  if (!hasText(value)) {
    return null;
  }
  return value.trim();
}

export function formatInsightLabel(value: string | null | undefined): string | null {
  const text = displayInsightText(value);
  if (!text) {
    return null;
  }
  return text.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function countBySeverity(
  severities: Array<string | null | undefined>,
): { severity: string; count: number }[] {
  const tally = new Map<string, number>();
  for (const value of severities) {
    const label = displayInsightText(value);
    if (!label) {
      continue;
    }
    tally.set(label, (tally.get(label) ?? 0) + 1);
  }
  return [...tally.entries()].map(([severity, count]) => ({ severity, count }));
}

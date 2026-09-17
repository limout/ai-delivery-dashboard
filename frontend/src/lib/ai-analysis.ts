export function toTextItems(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value
      .map((item) => (item == null ? "" : String(item).trim()))
      .filter((item) => item !== "");
  }
  if (typeof value === "string" && value.trim() !== "") {
    return [value.trim()];
  }
  return [];
}

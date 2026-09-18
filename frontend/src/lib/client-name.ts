const DEFAULT_CLIENT_NAME = "LIMOUT";

function isUsableClientName(value: string): boolean {
  if (!value) {
    return false;
  }
  if (/[\u0000-\u001F\u007F<>]/.test(value)) {
    return false;
  }
  return true;
}

export function resolveClientName(search: string): string {
  const params = new URLSearchParams(search);
  if (!params.has("client")) {
    return DEFAULT_CLIENT_NAME;
  }
  const decoded = (params.get("client") ?? "").trim();
  return isUsableClientName(decoded) ? decoded : DEFAULT_CLIENT_NAME;
}

export const CLIENT_NAME = resolveClientName(
  typeof window === "undefined" ? "" : window.location.search,
);

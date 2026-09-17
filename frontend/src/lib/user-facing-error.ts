export function userFacingError(error: unknown): string | null {
  if (!(error instanceof Error)) {
    return null;
  }
  const message = error.message.trim();
  if (!message) {
    return null;
  }
  if (
    message.includes("Traceback") ||
    message.includes("\n") ||
    message.length > 280
  ) {
    return null;
  }
  return message;
}

/**
 * Global Frontend Configuration.
 * Configurable API base URL with fallback to local proxy / relative URL.
 */
export const API_BASE_URL: string =
  (import.meta as any).env?.VITE_API_BASE_URL?.replace(/\/$/, '') || '';

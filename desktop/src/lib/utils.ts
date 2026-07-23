// API configuration for the FastAPI sidecar
export const SERVER_BASE = "http://127.0.0.1:9876";

// Re-export from api.ts for hooks to use
export const currentSettings = {
  apiBaseUrl: SERVER_BASE,
};

import { buildFallbackEvents, buildFallbackRun, fallbackCatalog } from "./demoData";
import type { CatalogResponse, DebateRunRequest, DebateRunSummary, RunEvent } from "./types";

const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const localHostnames = new Set(["localhost", "127.0.0.1", "::1"]);

export function shouldUseDebateApi(
  hostname = globalThis.location?.hostname ?? "",
  apiBaseUrl = configuredApiBaseUrl
): boolean {
  return apiBaseUrl.length > 0 || localHostnames.has(hostname);
}

function debateApiPath(path: string): string {
  return `${configuredApiBaseUrl}${path}`;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchCatalog(): Promise<CatalogResponse> {
  if (!shouldUseDebateApi()) {
    return fallbackCatalog;
  }

  try {
    const response = await fetch(debateApiPath("/api/models"));
    return await parseJsonResponse<CatalogResponse>(response);
  } catch {
    return fallbackCatalog;
  }
}

export async function startRun(request: DebateRunRequest): Promise<DebateRunSummary> {
  if (!shouldUseDebateApi()) {
    return buildFallbackRun(request.question, request.lane, request.panel);
  }

  try {
    const response = await fetch(debateApiPath("/api/runs"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request)
    });
    return await parseJsonResponse<DebateRunSummary>(response);
  } catch {
    return buildFallbackRun(request.question, request.lane, request.panel);
  }
}

export function getFallbackEvents(runId: string): RunEvent[] {
  return buildFallbackEvents(runId);
}

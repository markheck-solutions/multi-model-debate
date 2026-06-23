import { buildFallbackEvents, buildFallbackRun, fallbackCatalog } from "./demoData";
import type { CatalogResponse, DebateRunRequest, DebateRunSummary, RunEvent } from "./types";

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function fetchCatalog(): Promise<CatalogResponse> {
  try {
    const response = await fetch("/api/models");
    return await parseJsonResponse<CatalogResponse>(response);
  } catch {
    return fallbackCatalog;
  }
}

export async function startRun(request: DebateRunRequest): Promise<DebateRunSummary> {
  try {
    const response = await fetch("/api/runs", {
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

export type AuthMode = "api_key" | "demo" | "local" | "subscription";
export type ProviderKind = "anthropic" | "google" | "local" | "openai";
export type ProviderStatus = "connected" | "needs_setup" | "unavailable";
export type ReasoningEffort = "none" | "minimal" | "low" | "medium" | "high" | "xhigh";
export type RunLane = "demo" | "local";
export type RunPhase = "build" | "critique" | "debate" | "judge" | "final";
export type RunStatus = "ready" | "running" | "completed" | "failed" | "cancelled";
export type SeatRole = "builder" | "critic_a" | "critic_b" | "judge";

export interface ProviderAccount {
  id: string;
  provider: ProviderKind;
  label: string;
  auth_mode: AuthMode;
  status: ProviderStatus;
  secret_storage: string;
}

export interface ModelOption {
  id: string;
  account_id: string;
  provider: ProviderKind;
  label: string;
  cost_hint: string;
  reasoning_efforts: ReasoningEffort[];
}

export interface PanelSeat {
  role: SeatRole;
  label: string;
  required: boolean;
  enabled: boolean;
  account_id: string;
  model_id: string;
  reasoning_effort: ReasoningEffort;
  fresh_instance: boolean;
}

export interface PanelConfig {
  seats: PanelSeat[];
  diversity_label: string;
}

export interface CatalogResponse {
  accounts: ProviderAccount[];
  models: ModelOption[];
  default_panel: PanelConfig;
}

export interface DebateRunRequest {
  question: string;
  lane: RunLane;
  panel: PanelConfig;
  sync_report: boolean;
}

export interface DebateRunSummary {
  id: string;
  lane: RunLane;
  question: string;
  status: RunStatus;
  active_phase: RunPhase;
  panel: PanelConfig;
  final_report: string | null;
}

export interface RunEvent {
  run_id: string;
  phase: RunPhase;
  status: RunStatus;
  title: string;
  detail: string;
  progress: number;
}

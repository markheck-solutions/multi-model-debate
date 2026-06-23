"""Typed contracts for the GUI and local runner API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AuthMode(StrEnum):
    """How a provider account is authenticated."""

    API_KEY = "api_key"
    DEMO = "demo"
    LOCAL = "local"
    SUBSCRIPTION = "subscription"


class ProviderStatus(StrEnum):
    """Connection state shown in the AI tools rail."""

    CONNECTED = "connected"
    NEEDS_SETUP = "needs_setup"
    UNAVAILABLE = "unavailable"


class ProviderKind(StrEnum):
    """Supported provider families."""

    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    OPENAI = "openai"


class ReasoningEffort(StrEnum):
    """Reasoning effort options exposed in model seat controls."""

    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class RunLane(StrEnum):
    """Product lane for a run."""

    DEMO = "demo"
    LOCAL = "local"


class RunPhase(StrEnum):
    """Visible progress stages in the GUI timeline."""

    BUILD = "build"
    CRITIQUE = "critique"
    DEBATE = "debate"
    JUDGE = "judge"
    FINAL = "final"


class RunStatus(StrEnum):
    """Lifecycle state for GUI runs."""

    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeatRole(StrEnum):
    """Panel seats shown in the GUI."""

    BUILDER = "builder"
    CRITIC_A = "critic_a"
    CRITIC_B = "critic_b"
    JUDGE = "judge"


class ProviderAccount(BaseModel):
    """Non-secret provider account metadata."""

    id: str
    provider: ProviderKind
    label: str
    auth_mode: AuthMode
    status: ProviderStatus
    secret_storage: str = Field(
        default="not_stored",
        description="Plain-English storage status. Raw credentials are never returned.",
    )


class ModelOption(BaseModel):
    """Selectable model exposed to panel seat dropdowns."""

    id: str
    account_id: str
    provider: ProviderKind
    label: str
    cost_hint: str
    reasoning_efforts: list[ReasoningEffort]


class PanelSeat(BaseModel):
    """A single panel seat selection."""

    role: SeatRole
    label: str
    required: bool
    enabled: bool = True
    account_id: str
    model_id: str
    reasoning_effort: ReasoningEffort
    fresh_instance: bool = True


class PanelConfig(BaseModel):
    """Full panel selected by the user."""

    seats: list[PanelSeat]
    diversity_label: str = "Focused"


class DebateRunRequest(BaseModel):
    """Request to start a GUI run."""

    question: str = Field(min_length=3, max_length=8000)
    lane: RunLane = RunLane.DEMO
    panel: PanelConfig
    sync_report: bool = False


class DebateRunSummary(BaseModel):
    """Run summary shown in history and live preview."""

    id: str
    lane: RunLane
    question: str
    status: RunStatus
    active_phase: RunPhase
    panel: PanelConfig
    final_report: str | None = None


class HealthResponse(BaseModel):
    """Local runner health response."""

    status: str
    version: str
    lane: str


class CatalogResponse(BaseModel):
    """Model/account catalog returned to the GUI."""

    accounts: list[ProviderAccount]
    models: list[ModelOption]
    default_panel: PanelConfig


class RunEvent(BaseModel):
    """Live run event delivered over polling or WebSocket."""

    run_id: str
    phase: RunPhase
    status: RunStatus
    title: str
    detail: str
    progress: int = Field(ge=0, le=100)

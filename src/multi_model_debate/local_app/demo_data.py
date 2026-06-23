"""Demo catalog and run fixtures for the hosted portfolio lane."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from multi_model_debate.local_app.schemas import (
    AuthMode,
    DebateRunSummary,
    ModelOption,
    PanelConfig,
    PanelSeat,
    ProviderAccount,
    ProviderKind,
    ProviderStatus,
    ReasoningEffort,
    RunEvent,
    RunLane,
    RunPhase,
    RunStatus,
    SeatRole,
)


def build_demo_accounts() -> list[ProviderAccount]:
    """Return a non-secret demo account catalog."""
    return [
        ProviderAccount(
            id="demo-openai",
            provider=ProviderKind.OPENAI,
            label="ChatGPT / Codex",
            auth_mode=AuthMode.DEMO,
            status=ProviderStatus.CONNECTED,
        ),
        ProviderAccount(
            id="demo-anthropic",
            provider=ProviderKind.ANTHROPIC,
            label="Claude",
            auth_mode=AuthMode.DEMO,
            status=ProviderStatus.NEEDS_SETUP,
        ),
        ProviderAccount(
            id="demo-google",
            provider=ProviderKind.GOOGLE,
            label="Gemini",
            auth_mode=AuthMode.DEMO,
            status=ProviderStatus.NEEDS_SETUP,
        ),
        ProviderAccount(
            id="demo-local",
            provider=ProviderKind.LOCAL,
            label="Local model",
            auth_mode=AuthMode.LOCAL,
            status=ProviderStatus.UNAVAILABLE,
        ),
    ]


def build_demo_models() -> list[ModelOption]:
    """Return demo model choices for all panel dropdowns."""
    reasoning = [
        ReasoningEffort.LOW,
        ReasoningEffort.MEDIUM,
        ReasoningEffort.HIGH,
        ReasoningEffort.XHIGH,
    ]
    return [
        ModelOption(
            id="gpt-5-thinking",
            account_id="demo-openai",
            provider=ProviderKind.OPENAI,
            label="GPT-5 Thinking",
            cost_hint="Balanced",
            reasoning_efforts=reasoning,
        ),
        ModelOption(
            id="gpt-5-fast",
            account_id="demo-openai",
            provider=ProviderKind.OPENAI,
            label="GPT-5 Fast",
            cost_hint="Lower",
            reasoning_efforts=[ReasoningEffort.NONE, ReasoningEffort.LOW, ReasoningEffort.MEDIUM],
        ),
        ModelOption(
            id="claude-demo",
            account_id="demo-anthropic",
            provider=ProviderKind.ANTHROPIC,
            label="Claude demo seat",
            cost_hint="Setup needed",
            reasoning_efforts=[ReasoningEffort.MEDIUM],
        ),
        ModelOption(
            id="gemini-demo",
            account_id="demo-google",
            provider=ProviderKind.GOOGLE,
            label="Gemini demo seat",
            cost_hint="Setup needed",
            reasoning_efforts=[ReasoningEffort.MEDIUM],
        ),
    ]


def build_default_panel() -> PanelConfig:
    """Return a four-seat focused panel that uses one demo account."""
    seats = [
        PanelSeat(
            role=SeatRole.BUILDER,
            label="Builder",
            required=True,
            account_id="demo-openai",
            model_id="gpt-5-thinking",
            reasoning_effort=ReasoningEffort.MEDIUM,
        ),
        PanelSeat(
            role=SeatRole.CRITIC_A,
            label="Critic A",
            required=True,
            account_id="demo-openai",
            model_id="gpt-5-thinking",
            reasoning_effort=ReasoningEffort.HIGH,
        ),
        PanelSeat(
            role=SeatRole.CRITIC_B,
            label="Critic B",
            required=False,
            enabled=False,
            account_id="demo-openai",
            model_id="gpt-5-fast",
            reasoning_effort=ReasoningEffort.MEDIUM,
        ),
        PanelSeat(
            role=SeatRole.JUDGE,
            label="Judge",
            required=True,
            account_id="demo-openai",
            model_id="gpt-5-thinking",
            reasoning_effort=ReasoningEffort.MEDIUM,
        ),
    ]
    return PanelConfig(seats=seats, diversity_label="Focused")


def create_demo_run(question: str, panel: PanelConfig) -> DebateRunSummary:
    """Create a completed demo run summary for the portfolio lane."""
    return DebateRunSummary(
        id=f"demo-{uuid4().hex[:10]}",
        lane=RunLane.DEMO,
        question=question,
        status=RunStatus.COMPLETED,
        active_phase=RunPhase.FINAL,
        panel=panel,
        final_report=build_demo_report(question, panel),
    )


def build_demo_events(run_id: str) -> list[RunEvent]:
    """Create deterministic timeline events for a demo run."""
    return [
        RunEvent(
            run_id=run_id,
            phase=RunPhase.BUILD,
            status=RunStatus.RUNNING,
            title="Builder framed the decision",
            detail=(
                "Converted the question into a concrete plan, assumptions, and decision criteria."
            ),
            progress=18,
        ),
        RunEvent(
            run_id=run_id,
            phase=RunPhase.CRITIQUE,
            status=RunStatus.RUNNING,
            title="Critic A found weak spots",
            detail=(
                "Flagged cost exposure, rollout timing, support load, and unclear success metrics."
            ),
            progress=42,
        ),
        RunEvent(
            run_id=run_id,
            phase=RunPhase.DEBATE,
            status=RunStatus.RUNNING,
            title="Panel compared tradeoffs",
            detail="Focused the debate on which risks block launch versus which can be monitored.",
            progress=68,
        ),
        RunEvent(
            run_id=run_id,
            phase=RunPhase.JUDGE,
            status=RunStatus.RUNNING,
            title="Judge selected the strongest argument",
            detail=(
                "Weighted evidence quality over confidence and separated "
                "facts from preference calls."
            ),
            progress=88,
        ),
        RunEvent(
            run_id=run_id,
            phase=RunPhase.FINAL,
            status=RunStatus.COMPLETED,
            title="Final report ready",
            detail=(
                "Recommendation, blockers, decision points, and next actions are ready to review."
            ),
            progress=100,
        ),
    ]


def iter_demo_events(run_id: str) -> Iterable[RunEvent]:
    """Yield demo events in display order."""
    yield from build_demo_events(run_id)


def build_demo_report(question: str, panel: PanelConfig) -> str:
    """Return a polished sample final report."""
    critic_b = next(seat for seat in panel.seats if seat.role is SeatRole.CRITIC_B)
    panel_mode = "two-critic debate" if critic_b.enabled else "focused review"
    return (
        "## Final Position\n\n"
        f"**Question:** {question}\n\n"
        f"**Panel mode:** {panel_mode} with {panel.diversity_label.lower()} diversity.\n\n"
        "**Recommendation:** Conditional approval. The idea is strong enough to continue, "
        "but only after launch criteria, rollback ownership, and cost controls "
        "are written down.\n\n"
        "**Top risks:**\n"
        "1. Success criteria are still too broad.\n"
        "2. The rollout plan needs a clear owner for support and rollback.\n"
        "3. Cost exposure should be capped before real users depend on it.\n\n"
        "**Next action:** Turn the decision into a one-page launch brief and run one more "
        "debate after the missing owner and budget details are filled in.\n"
    )

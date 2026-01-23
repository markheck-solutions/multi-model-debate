"""Main orchestration for the adversarial review workflow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from rich.console import Console

from multi_model_debate.exceptions import ReviewError
from multi_model_debate.models import (
    CLIModelBackend,
    create_cli_backend,
    create_strategist_backend,
)
from multi_model_debate.phases import (
    BaselinePhase,
    DebatePhase,
    DefensePhase,
    FinalPositionPhase,
    JudgePhase,
    PeerReviewPhase,
)
from multi_model_debate.pre_debate import PreDebateProtocol, ProtocolResult
from multi_model_debate.roles import RoleAssignment, assign_roles, get_critic_pair
from multi_model_debate.storage.run import (
    PromptHashMismatchError,
    RunContext,
    create_run,
    create_run_from_content,
    find_latest_incomplete_run,
    load_run,
    validate_integrity_hash,
    verify_game_plan_integrity,
)

if TYPE_CHECKING:
    from multi_model_debate.config import Config


class RunStatus(TypedDict):
    """Status information for a run."""

    run_dir: str
    status: str
    completed_phases: list[str]
    game_plan: str | None


console = Console()


class Orchestrator:
    """Main orchestrator for the adversarial review workflow.

    Manages the 6-phase review process, handles checkpointing,
    and coordinates model invocations.

    Models are loaded dynamically from config.models.available.
    Roles (strategist, critics, judge) are assigned dynamically based on
    who initiated the debate.
    """

    def __init__(self, config: Config, runs_dir: Path) -> None:
        """Initialize the orchestrator.

        Args:
            config: Configuration settings.
            runs_dir: Directory for storing runs.
        """
        self.config = config
        self.runs_dir = runs_dir

        # Dynamic role assignment based on config
        self.roles: RoleAssignment = assign_roles(config)

        # Determine which models to load:
        # - All role models (strategist, critics, judge)
        # - Plus any additional in models.available
        models_to_load: set[str] = set(self.roles.critics)
        models_to_load.add(self.roles.strategist)
        models_to_load.add(self.roles.judge)
        models_to_load.update(config.models.available)

        # Load models dynamically from config
        self.models: dict[str, CLIModelBackend] = {}
        for name in models_to_load:
            try:
                cli_config = config.cli[name]
                self.models[name] = create_cli_backend(
                    name=name,
                    cli_config=cli_config,
                    retry_config=config.retry,
                    min_response_length=config.models.min_response_length,
                    default_timeout=config.models.default_timeout,
                )
            except KeyError as err:
                raise ReviewError(
                    f"No CLI configuration for model '{name}'. Add [cli.{name}] section to config."
                ) from err
        console.print(
            f"[dim]Roles: strategist={self.roles.strategist}, "
            f"critics={self.roles.critics}, judge={self.roles.judge}[/dim]"
        )

        # Get the two critics for debate phases
        self._critic_a_name, self._critic_b_name = get_critic_pair(self.roles)
        critic_a = self.models.get(self._critic_a_name)
        critic_b = self.models.get(self._critic_b_name)
        if critic_a is None:
            raise ReviewError(f"Critic model '{self._critic_a_name}' not available")
        if critic_b is None:
            raise ReviewError(f"Critic model '{self._critic_b_name}' not available")
        self.critic_a: CLIModelBackend = critic_a
        self.critic_b: CLIModelBackend = critic_b

        # Judge model (same family as strategist, isolated instance for judging critics)
        judge = self.models.get(self.roles.judge)
        if judge is None:
            raise ReviewError(f"Judge model '{self.roles.judge}' not available")
        self.judge_model: CLIModelBackend = judge

        # Strategist backend for phases 5 & 6 (fully automated via CLI)
        # Uses the strategist's CLI config, not hardcoded to any specific model.
        # See REQUIREMENTS_V2.md Section 4 for rationale on full automation.
        self.strategist = create_strategist_backend(
            cli_config=config.cli[self.roles.strategist],
            retry_config=config.retry,
            min_response_length=config.models.min_response_length,
            default_timeout=config.models.default_timeout,
        )

    def start(self, game_plan: Path) -> RunContext:
        """Start a new adversarial review.

        Args:
            game_plan: Path to the game plan file.

        Returns:
            RunContext for the new run.

        Raises:
            ReviewError: If game plan doesn't exist.
        """
        if not game_plan.exists():
            raise ReviewError(f"Game plan not found: {game_plan}")

        context = create_run(game_plan, self.runs_dir, self.config)
        console.print("[bold green]Starting new review[/bold green]")
        console.print(f"  Run: {context.run_dir}")
        console.print(f"  Game plan: {game_plan}")
        console.print()

        return context

    def start_from_content(self, content: str) -> RunContext:
        """Start a new adversarial review from content string.

        Args:
            content: The game plan content as a string.

        Returns:
            RunContext for the new run.

        Raises:
            ReviewError: If content is empty.
        """
        if not content or not content.strip():
            raise ReviewError("Game plan content is empty")

        context = create_run_from_content(content, self.runs_dir, self.config)
        console.print("[bold green]Starting new review[/bold green]")
        console.print(f"  Run: {context.run_dir}")
        console.print("  Game plan: (stdin)")
        console.print()

        return context

    def run_pre_debate_protocol(
        self,
        context: RunContext | None = None,
        skip_protocol: bool = False,
    ) -> ProtocolResult | None:
        """Run the pre-debate protocol.

        The protocol injects the current date context so models can
        assess proposal relevance against current technology.

        Args:
            context: Run context for tracking completion state.
            skip_protocol: Skip the entire protocol.

        Returns:
            ProtocolResult if run, None if skipped.
        """
        # Check if already complete (on resume)
        if context is not None and context.is_pre_debate_complete():
            console.print("[dim]Pre-debate protocol already complete[/dim]")
            return None

        # Check if protocol is enabled
        if skip_protocol or not self.config.pre_debate.enabled:
            console.print("[dim]Pre-debate protocol skipped[/dim]")
            # Mark complete even when skipped so resume doesn't re-run
            if context is not None:
                context.mark_pre_debate_complete()
            return None

        # Run the protocol
        protocol = PreDebateProtocol(models=self.models, config=self.config)
        result = protocol.run()

        # Mark complete
        if context is not None:
            context.mark_pre_debate_complete()

        return result

    def resume(self, run_dir: Path | None = None) -> RunContext:
        """Resume an incomplete review.

        Args:
            run_dir: Specific run to resume. If None, finds latest incomplete.

        Returns:
            RunContext for the resumed run.

        Raises:
            ReviewError: If no incomplete run found.
            PromptHashMismatchError: If prompts have changed since debate started.
        """
        if run_dir is None:
            run_dir = find_latest_incomplete_run(self.runs_dir)

        if run_dir is None:
            raise ReviewError("No incomplete run found to resume")

        # CRITICAL: Validate prompts, config, and env vars haven't changed
        # See REQUIREMENTS_V2.md Section 5 - NO "continue anyway" option
        if not validate_integrity_hash(run_dir):
            console.print()
            console.print("[bold red]ERROR: Integrity check failed[/bold red]")
            console.print()
            console.print(
                "[yellow]Prompts, config, or environment have changed "
                "since this debate started.[/yellow]"
            )
            console.print(
                "[yellow]A debate with changed state produces unreliable results.[/yellow]"
            )
            console.print("[yellow]Must restart debate from beginning.[/yellow]")
            console.print()
            raise PromptHashMismatchError(run_dir)

        context = load_run(run_dir, self.config)

        # Verify game plan integrity (warning only, not blocking)
        if not verify_game_plan_integrity(context):
            console.print("[yellow]WARNING: Game plan has changed since run started[/yellow]")

        console.print("[bold green]Resuming review[/bold green]")
        console.print(f"  Run: {context.run_dir}")
        console.print(f"  Completed: {context.completed_phases()}")
        console.print()

        return context

    def execute(self, context: RunContext) -> None:
        """Execute all phases of the review.

        Args:
            context: The run context.

        Raises:
            ReviewError: If any phase fails.
        """
        # Set error log for all CLI backends
        for model in self.models.values():
            model.error_log = context.error_log

        completed = context.completed_phases()

        try:
            # Phase 1: Baseline Critiques (from both critics)
            phase1 = BaselinePhase(
                run_dir=context.run_dir,
                config=self.config,
                critic_a=self.critic_a,
                critic_b=self.critic_b,
                critic_a_name=self._critic_a_name,
                critic_b_name=self._critic_b_name,
            )
            self._run_phase(phase1, context, completed)

            # Phase 2: Critic vs Critic Debate
            phase2 = DebatePhase(
                run_dir=context.run_dir,
                config=self.config,
                critic_a=self.critic_a,
                critic_b=self.critic_b,
                critic_a_name=self._critic_a_name,
                critic_b_name=self._critic_b_name,
            )
            self._run_phase(phase2, context, completed)

            # Phase 3: Winner Determination (by Judge)
            phase3 = JudgePhase(
                run_dir=context.run_dir,
                config=self.config,
                judge=self.judge_model,
                critic_a_name=self._critic_a_name,
                critic_b_name=self._critic_b_name,
            )
            self._run_phase(phase3, context, completed)

            # Phase 4: Peer Review (by winning critic)
            phase4 = PeerReviewPhase(
                run_dir=context.run_dir,
                config=self.config,
                critic_a=self.critic_a,
                critic_b=self.critic_b,
                critic_a_name=self._critic_a_name,
                critic_b_name=self._critic_b_name,
            )
            self._run_phase(phase4, context, completed)

            # Phase 5: Strategist Defense (against winning critic)
            phase5 = DefensePhase(
                run_dir=context.run_dir,
                config=self.config,
                strategist=self.strategist,
                critic_a=self.critic_a,
                critic_b=self.critic_b,
                critic_a_name=self._critic_a_name,
                critic_b_name=self._critic_b_name,
            )
            self._run_phase(phase5, context, completed)

            # Phase 6: Final Position (by Strategist)
            phase6 = FinalPositionPhase(
                run_dir=context.run_dir,
                config=self.config,
                strategist=self.strategist,
            )
            self._run_phase(phase6, context, completed)

            # Mark complete and display Final Position
            context.log_status("COMPLETED")
            phase6.display_final_position()

            # Human notification at the END - this is the only notification
            # per REQUIREMENTS_V2.md Section 4
            self._notify("Final Position ready for your review")

        except Exception as e:
            context.log_status(f"FAILED: {e}")
            self._notify(f"Review failed: {e}")
            raise

    def _run_phase(
        self,
        phase: BaselinePhase
        | DebatePhase
        | JudgePhase
        | PeerReviewPhase
        | DefensePhase
        | FinalPositionPhase,
        context: RunContext,
        completed: set[str],
    ) -> None:
        """Run a single phase with checkpoint handling.

        Args:
            phase: The phase to run.
            context: The run context.
            completed: Set of already-completed phase names.

        Note: Human notifications only happen at the END when Final Position
        is ready, not after each phase. See REQUIREMENTS_V2.md Section 4.
        """
        if phase.name in completed and phase.is_complete():
            console.print(f"[dim]Skipping {phase.display_name} (complete)[/dim]")
            return

        console.print(f"[bold]Running {phase.display_name}...[/bold]")
        phase.run()

        if not phase.is_complete():
            raise ReviewError(f"{phase.display_name} failed to produce valid artifacts")

        context.mark_complete(phase.name)
        # NOTE: No notification here - human is only notified at the END
        # when Final Position is ready. See REQUIREMENTS_V2.md Section 4.

    def _notify(self, message: str) -> None:
        """Send a desktop notification if enabled.

        Args:
            message: The notification message.
        """
        if not self.config.notification.enabled:
            return

        import subprocess

        try:
            subprocess.run(
                [self.config.notification.command, "Adversarial Review", message],
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            print(f"Warning: Notification failed - {e}", file=sys.stderr)

    def status(self) -> RunStatus | None:
        """Get the status of the latest run.

        Returns:
            Status dictionary or None if no runs exist.
        """
        if not self.runs_dir.exists():
            return None

        run_dirs = sorted(
            [d for d in self.runs_dir.iterdir() if d.is_dir()],
            reverse=True,
        )

        if not run_dirs:
            return None

        run_dir = run_dirs[0]
        status_file = run_dir / "status.txt"
        checkpoint_file = run_dir / "checkpoint.txt"
        manifest_file = run_dir / "manifest.json"

        result: RunStatus = {
            "run_dir": str(run_dir),
            "status": "unknown",
            "completed_phases": [],
            "game_plan": None,
        }

        if status_file.exists():
            content = status_file.read_text()
            if "COMPLETED" in content:
                result["status"] = "completed"
            elif "FAILED" in content:
                result["status"] = "failed"
            else:
                result["status"] = "in_progress"

        if checkpoint_file.exists():
            content = checkpoint_file.read_text().strip()
            if content:
                result["completed_phases"] = content.split("\n")

        if manifest_file.exists():
            import json

            manifest = json.loads(manifest_file.read_text())
            result["game_plan"] = manifest.get("game_plan")

        return result

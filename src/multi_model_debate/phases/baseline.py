"""Phase 1: Independent baseline critiques from critics."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console

from multi_model_debate.phases.base import Phase, PhaseArtifact

if TYPE_CHECKING:
    from multi_model_debate.config import Config
    from multi_model_debate.models.protocols import ModelBackend

console = Console()


class BaselinePhase(Phase):
    """Phase 1: Critics independently critique the proposal.

    Each critic uses an adversarial "assume flawed" persona with different
    focus areas. Critics do NOT see each other's critiques.
    """

    def __init__(
        self,
        run_dir: Path,
        config: Config,
        *,
        critic_a: ModelBackend,
        critic_b: ModelBackend,
        critic_a_name: str,
        critic_b_name: str,
    ) -> None:
        """Initialize the baseline phase.

        Args:
            run_dir: Directory for this run's artifacts.
            config: Configuration settings.
            critic_a: First critic model backend.
            critic_b: Second critic model backend.
            critic_a_name: Display name for first critic (e.g., "codex").
            critic_b_name: Display name for second critic (e.g., "gemini").
        """
        super().__init__(run_dir, config)
        self.critic_a = critic_a
        self.critic_b = critic_b
        self.critic_a_name = critic_a_name
        self.critic_b_name = critic_b_name

    @property
    def name(self) -> str:
        """Phase identifier."""
        return "PHASE_1"

    @property
    def display_name(self) -> str:
        """Human-readable phase name."""
        return "Baseline Critiques"

    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts required for phase completion."""
        return [
            self.artifact(f"p1_{self.critic_a_name}_baseline", is_json=True),
            self.artifact(f"p1_{self.critic_b_name}_baseline", is_json=True),
        ]

    def run(self) -> None:
        """Execute the baseline phase.

        Generates independent critiques from both critics in parallel.
        Skips already-completed artifacts on resume.
        """
        game_plan = self.get_game_plan()
        # Dynamic lens selection based on model
        critic_a_lens = self.render_template("critic_1_lens.md.j2")
        critic_b_lens = self.render_template("critic_2_lens.md.j2")

        critic_a_artifact = self.artifact(f"p1_{self.critic_a_name}_baseline", is_json=True)
        critic_b_artifact = self.artifact(f"p1_{self.critic_b_name}_baseline", is_json=True)

        # Track which critics need to run
        futures: dict[Any, tuple[str, PhaseArtifact]] = {}

        with ThreadPoolExecutor(max_workers=2) as executor:
            if not critic_a_artifact.is_valid():
                console.print(f"  [cyan]{self.critic_a_name} baseline critique...[/cyan]")
                critic_a_prompt = self.render_template(
                    "baseline_critique.md.j2",
                    lens_prompt=critic_a_lens,
                    game_plan=game_plan,
                )
                future = executor.submit(self.critic_a.generate, critic_a_prompt)
                futures[future] = (self.critic_a_name, critic_a_artifact)
            else:
                console.print(f"  [dim]{self.critic_a_name} baseline (cached)[/dim]")

            if not critic_b_artifact.is_valid():
                console.print(f"  [cyan]{self.critic_b_name} baseline critique...[/cyan]")
                critic_b_prompt = self.render_template(
                    "baseline_critique.md.j2",
                    lens_prompt=critic_b_lens,
                    game_plan=game_plan,
                )
                future = executor.submit(self.critic_b.generate, critic_b_prompt)
                futures[future] = (self.critic_b_name, critic_b_artifact)
            else:
                console.print(f"  [dim]{self.critic_b_name} baseline (cached)[/dim]")

            # Wait for parallel calls to complete
            for future in as_completed(futures):
                name, artifact = futures[future]
                response: str = future.result()
                artifact.write(response)
                console.print(f"  [green]{name} baseline complete[/green]")

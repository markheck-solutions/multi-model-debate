"""Phase 2: Critic vs Critic adversarial debate."""

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


class DebatePhase(Phase):
    """Phase 2: Critics debate each other.

    Multiple rounds of alternating critiques. Each round only sees
    the previous round's response (rolling window) to prevent token saturation.
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
        """Initialize the debate phase.

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
        self._rounds = config.debate.critic_rounds

    @property
    def name(self) -> str:
        """Phase identifier."""
        return "PHASE_2"

    @property
    def display_name(self) -> str:
        """Human-readable phase name with dynamic model names."""
        return f"{self.critic_a_name} vs {self.critic_b_name} Debate"

    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts required for phase completion."""
        artifacts = []
        for r in range(1, self._rounds + 1):
            artifacts.append(self.artifact(f"p2_r{r}_{self.critic_a_name}", is_json=True))
            artifacts.append(self.artifact(f"p2_r{r}_{self.critic_b_name}", is_json=True))
        return artifacts

    def run(self) -> None:
        """Execute the debate phase.

        Runs multiple rounds where both critics respond in parallel.
        Each critic responds to the other's PREVIOUS round output.
        Uses rolling window context (only previous round's response).
        """
        game_plan = self.get_game_plan()
        # Dynamic lens selection based on model
        critic_a_lens = self.render_template("critic_1_lens.md.j2")
        critic_b_lens = self.render_template("critic_2_lens.md.j2")

        # Load baselines as starting point
        critic_a_last = self.artifact(f"p1_{self.critic_a_name}_baseline", is_json=True).read()
        critic_b_last = self.artifact(f"p1_{self.critic_b_name}_baseline", is_json=True).read()

        for round_num in range(1, self._rounds + 1):
            console.print(f"  [bold]Round {round_num}/{self._rounds}[/bold]")

            critic_a_artifact = self.artifact(f"p2_r{round_num}_{self.critic_a_name}", is_json=True)
            critic_b_artifact = self.artifact(f"p2_r{round_num}_{self.critic_b_name}", is_json=True)

            # Track which critics need to run
            futures: dict[Any, tuple[str, PhaseArtifact]] = {}
            round_label = "Baseline" if round_num == 1 else f"Round {round_num - 1}"

            with ThreadPoolExecutor(max_workers=2) as executor:
                # Critic A responds to Critic B's previous output
                if not critic_a_artifact.is_valid():
                    console.print(f"    [cyan]{self.critic_a_name} responding...[/cyan]")
                    critic_a_prompt = self.render_template(
                        "debate_round.md.j2",
                        lens_prompt=critic_a_lens,
                        game_plan=game_plan,
                        opponent_name=self.critic_b_name.upper(),
                        round_label=round_label,
                        opponent_response=critic_b_last,
                    )
                    future = executor.submit(self.critic_a.generate, critic_a_prompt)
                    futures[future] = (self.critic_a_name, critic_a_artifact)
                else:
                    console.print(f"    [dim]{self.critic_a_name} (cached)[/dim]")

                # Critic B responds to Critic A's previous output
                if not critic_b_artifact.is_valid():
                    console.print(f"    [cyan]{self.critic_b_name} responding...[/cyan]")
                    critic_b_prompt = self.render_template(
                        "debate_round.md.j2",
                        lens_prompt=critic_b_lens,
                        game_plan=game_plan,
                        opponent_name=self.critic_a_name.upper(),
                        round_label=round_label,
                        opponent_response=critic_a_last,
                    )
                    future = executor.submit(self.critic_b.generate, critic_b_prompt)
                    futures[future] = (self.critic_b_name, critic_b_artifact)
                else:
                    console.print(f"    [dim]{self.critic_b_name} (cached)[/dim]")

                # Wait for parallel calls to complete
                for future in as_completed(futures):
                    name, artifact = futures[future]
                    response: str = future.result()
                    artifact.write(response)
                    console.print(f"    [green]{name} done[/green]")

            # Update "last" responses for next round
            critic_a_last = critic_a_artifact.read()
            critic_b_last = critic_b_artifact.read()

    def get_final_positions(self) -> tuple[str, str]:
        """Get the final positions from the debate.

        Returns:
            Tuple of (critic_a_final, critic_b_final) responses.
        """
        critic_a_final = self.artifact(
            f"p2_r{self._rounds}_{self.critic_a_name}", is_json=True
        ).read()
        critic_b_final = self.artifact(
            f"p2_r{self._rounds}_{self.critic_b_name}", is_json=True
        ).read()
        return critic_a_final, critic_b_final

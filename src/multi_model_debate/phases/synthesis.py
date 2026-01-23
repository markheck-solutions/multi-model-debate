"""Phase 4: Winner produces Peer Review for Strategist to defend against."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from multi_model_debate.exceptions import PhaseError
from multi_model_debate.phases.base import Phase, PhaseArtifact

if TYPE_CHECKING:
    from multi_model_debate.config import Config
    from multi_model_debate.models.protocols import ModelBackend

console = Console()


class PeerReviewPhase(Phase):
    """Phase 4: The debate winner produces the Peer Review.

    The winner consolidates their critiques and adopts valid points
    from the loser, producing a structured Peer Review for the Strategist to defend against.
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
        """Initialize the peer review phase.

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
        return "PHASE_4"

    @property
    def display_name(self) -> str:
        """Human-readable phase name."""
        return "Peer Review"

    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts required for phase completion."""
        return [self.artifact("p4_peer_review")]

    def run(self) -> None:
        """Execute the peer review phase.

        The winner produces a comprehensive Peer Review for the Strategist to defend against.
        """
        peer_review_artifact = self.artifact("p4_peer_review")

        if not peer_review_artifact.is_valid():
            winner_name = self._get_winner_name()
            console.print(f"  [cyan]{winner_name} generating peer review...[/cyan]")

            game_plan = self.get_game_plan()
            synthesis_template = self.render_template("synthesis_template.md.j2")

            # Get final positions from debate
            critic_a_final = self.artifact(
                f"p2_r{self._rounds}_{self.critic_a_name}", is_json=True
            ).read()
            critic_b_final = self.artifact(
                f"p2_r{self._rounds}_{self.critic_b_name}", is_json=True
            ).read()

            # Determine winner/loser based on winner name
            if winner_name == self.critic_a_name:
                winner_final = critic_a_final
                loser_final = critic_b_final
                winner_model = self.critic_a
            else:
                winner_final = critic_b_final
                loser_final = critic_a_final
                winner_model = self.critic_b

            prompt = self.render_template(
                "synthesis_prompt.md.j2",
                synthesis_template=synthesis_template,
                game_plan=game_plan,
                winner_final=winner_final,
                loser_final=loser_final,
            )

            response = winner_model.generate(prompt)  # Uses per-model timeout
            peer_review_artifact.write(response)
            console.print("  [green]Peer review complete[/green]")
        else:
            console.print("  [dim]Peer review (cached)[/dim]")

    def _get_winner_name(self) -> str:
        """Get the winner's model name from Phase 3.

        Returns:
            The critic name (e.g., "codex" or "gemini").

        Raises:
            PhaseError: If winner file doesn't exist or format is invalid.
        """
        winner_path = self.run_dir / "p3_winner.txt"
        if not winner_path.exists():
            raise PhaseError("Winner file not found - Phase 3 must complete first")

        content = winner_path.read_text().strip()
        if content.startswith("WINNER="):
            return content.split("=")[1].strip()

        raise PhaseError(f"Invalid winner file format: {content}")

    def get_peer_review(self) -> str:
        """Get the peer review content.

        Returns:
            The peer review text.
        """
        return self.artifact("p4_peer_review").read()

    def get_winner_model(self) -> ModelBackend:
        """Get the winning model backend.

        Returns:
            The winning critic backend.
        """
        winner_name = self._get_winner_name()
        return self.critic_a if winner_name == self.critic_a_name else self.critic_b

    def get_winner_lens(self) -> str:
        """Get the winner's lens prompt.

        Returns:
            The lens template content for the winning critic.
        """
        winner_name = self._get_winner_name()
        # Use critic A's lens for critic A, critic B's lens for critic B
        if winner_name == self.critic_a_name:
            template = "critic_1_lens.md.j2"
        else:
            template = "critic_2_lens.md.j2"
        return self.render_template(template)

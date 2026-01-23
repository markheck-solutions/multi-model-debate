"""Phase 5: Strategist defends the proposal against the winner's Peer Review."""

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


class DefensePhase(Phase):
    """Phase 5: Strategist defends the proposal against the debate winner.

    Fully automated phase where Strategist responds via CLI invocation.
    The Strategist is the AI that authored the game plan and has full context.
    """

    def __init__(
        self,
        run_dir: Path,
        config: Config,
        strategist: ModelBackend,
        *,
        critic_a: ModelBackend,
        critic_b: ModelBackend,
        critic_a_name: str,
        critic_b_name: str,
    ) -> None:
        """Initialize the defense phase.

        Args:
            run_dir: Directory for this run's artifacts.
            config: Configuration settings.
            strategist: Strategist model backend (uses CLI invocation).
            critic_a: First critic model backend.
            critic_b: Second critic model backend.
            critic_a_name: Display name for first critic (e.g., "codex").
            critic_b_name: Display name for second critic (e.g., "gemini").
        """
        super().__init__(run_dir, config)
        self.strategist = strategist
        self.critic_a = critic_a
        self.critic_b = critic_b
        self.critic_a_name = critic_a_name
        self.critic_b_name = critic_b_name
        self._rounds = config.debate.strategist_rounds

    @property
    def name(self) -> str:
        """Phase identifier."""
        return "PHASE_5"

    @property
    def display_name(self) -> str:
        """Human-readable phase name."""
        return "Strategist Defense"

    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts required for phase completion.

        Phase 5 requires:
        - p5_r0_strategist.md (initial Strategist defense)
        - p5_r{1..N}_winner.md (winner's responses)
        - p5_r{1..N}_strategist.md (Strategist's responses)
        """
        artifacts = [self.artifact("p5_r0_strategist")]
        for r in range(1, self._rounds + 1):
            artifacts.append(self.artifact(f"p5_r{r}_winner"))
            artifacts.append(self.artifact(f"p5_r{r}_strategist"))
        return artifacts

    def run(self) -> None:
        """Execute the defense phase.

        Strategist defends against the winner's Peer Review, then multiple
        rounds of back-and-forth debate. All responses are automated via CLI.
        """
        winner_name = self._get_winner_name()
        winner_model = self.critic_a if winner_name == self.critic_a_name else self.critic_b
        winner_lens = self._get_winner_lens(winner_name)

        game_plan = self.get_game_plan()
        strategist_lens = self.render_template("strategist_proxy_lens.md.j2")
        peer_review = self.artifact("p4_peer_review").read()

        # Initial Strategist defense against Peer Review
        strategist_initial = self.artifact("p5_r0_strategist")
        if not strategist_initial.is_valid():
            console.print("  [bold cyan]Round 0: Strategist Initial Defense[/bold cyan]")
            prompt = self.render_template(
                "defense_initial.md.j2",
                strategist_lens=strategist_lens,
                peer_review=peer_review,
            )
            response = self.strategist.generate(prompt)  # Uses per-model timeout
            strategist_initial.write(response)
            # Journal the Strategist response for audit trail
            self.journal_response(round_num=0, response=response)
            console.print("  [green]Strategist initial defense complete[/green]")
        else:
            console.print("  [dim]Round 0: Strategist Initial (cached)[/dim]")

        strategist_last = strategist_initial.read()

        # Debate rounds
        for round_num in range(1, self._rounds + 1):
            console.print(f"  [bold]Round {round_num}/{self._rounds}[/bold]")

            # Winner responds to Strategist
            winner_artifact = self.artifact(f"p5_r{round_num}_winner")
            if not winner_artifact.is_valid():
                console.print(f"    [cyan]{winner_name} responding...[/cyan]")
                round_label = "Initial" if round_num == 1 else f"Round {round_num - 1}"
                prompt = self.render_template(
                    "winner_response.md.j2",
                    winner_lens=winner_lens,
                    game_plan=game_plan,
                    peer_review=peer_review,
                    round_label=round_label,
                    strategist_response=strategist_last,
                )
                response = winner_model.generate(prompt)  # Uses per-model timeout
                winner_artifact.write(response)
                console.print(f"    [green]{winner_name} done[/green]")
            else:
                console.print(f"    [dim]{winner_name} (cached)[/dim]")

            winner_last = winner_artifact.read()

            # Strategist responds to winner
            strategist_artifact = self.artifact(f"p5_r{round_num}_strategist")
            if not strategist_artifact.is_valid():
                console.print("    [bold cyan]Strategist responding...[/bold cyan]")
                prompt = self.render_template(
                    "defense_round.md.j2",
                    strategist_lens=strategist_lens,
                    round_number=round_num,
                    winner_response=winner_last,
                )
                response = self.strategist.generate(prompt)  # Uses per-model timeout
                strategist_artifact.write(response)
                # Journal the Strategist response for audit trail
                self.journal_response(round_num=round_num, response=response)
                console.print("    [green]Strategist done[/green]")
            else:
                console.print("    [dim]Strategist (cached)[/dim]")

            strategist_last = strategist_artifact.read()

    def _get_winner_name(self) -> str:
        """Get the winner's model name from Phase 3."""
        winner_path = self.run_dir / "p3_winner.txt"
        if not winner_path.exists():
            raise PhaseError("Winner file not found")
        content = winner_path.read_text().strip()
        if content.startswith("WINNER="):
            return content.split("=")[1].strip()
        raise PhaseError(f"Invalid winner file: {content}")

    def _get_winner_lens(self, winner_name: str) -> str:
        """Get the winner's lens prompt."""
        # Use critic A's lens for critic A, critic B's lens for critic B
        if winner_name == self.critic_a_name:
            template = "critic_1_lens.md.j2"
        else:
            template = "critic_2_lens.md.j2"
        return self.render_template(template)

    def get_final_responses(self) -> tuple[str, str]:
        """Get the final responses from the defense.

        Returns:
            Tuple of (final_winner_response, final_strategist_response).
        """
        final_winner = self.artifact(f"p5_r{self._rounds}_winner").read()
        final_strategist = self.artifact(f"p5_r{self._rounds}_strategist").read()
        return final_winner, final_strategist

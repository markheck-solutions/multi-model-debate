"""Phase 3: Judge determines the winner of the critic debate."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from multi_model_debate.exceptions import PhaseError
from multi_model_debate.phases.base import Phase, PhaseArtifact

if TYPE_CHECKING:
    from multi_model_debate.config import Config
    from multi_model_debate.models.protocols import ModelBackend

console = Console()


class JudgePhase(Phase):
    """Phase 3: Judge determines which critic won the debate.

    Judge evaluates based on issue quality, consistency, evidence,
    and novelty - NOT rhetorical persuasiveness.

    DESIGN: Judge = Strategist's model family (isolated instance)

    The Judge evaluates CRITICS' arguments, not the plan directly.
    However, the Judge must read the plan to assess critique validity.
    Since Judge is different family from both Critics, no bias.

    See REQUIREMENTS_V2.md for full rationale and evidence.
    """

    def __init__(
        self,
        run_dir: Path,
        config: Config,
        *,
        judge: ModelBackend,
        critic_a_name: str,
        critic_b_name: str,
    ) -> None:
        """Initialize the judge phase.

        Args:
            run_dir: Directory for this run's artifacts.
            config: Configuration settings.
            judge: Judge model backend (non-interactive).
            critic_a_name: Display name for first critic (e.g., "codex").
            critic_b_name: Display name for second critic (e.g., "gemini").
        """
        super().__init__(run_dir, config)
        self.judge = judge
        self.critic_a_name = critic_a_name
        self.critic_b_name = critic_b_name
        self._rounds = config.debate.critic_rounds

    @property
    def name(self) -> str:
        """Phase identifier."""
        return "PHASE_3"

    @property
    def display_name(self) -> str:
        """Human-readable phase name."""
        return "Winner Determination"

    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts required for phase completion."""
        return [
            self.artifact("p3_winner_decision"),
            PhaseArtifact(
                name="p3_winner",
                path=self.run_dir / "p3_winner.txt",
                min_length=3,  # Critic name (e.g., "codex", "gemini")
            ),
        ]

    def run(self) -> None:
        """Execute the judge phase.

        Judge evaluates final critic positions and determines the winner.
        """
        decision_artifact = self.artifact("p3_winner_decision")
        winner_artifact = PhaseArtifact(
            name="p3_winner",
            path=self.run_dir / "p3_winner.txt",
            min_length=3,
        )

        if not decision_artifact.is_valid():
            console.print("  [cyan]Judge evaluating debate...[/cyan]")

            game_plan = self.get_game_plan()
            judge_template = self.render_template("judge.md.j2")

            # Get final positions from debate
            critic_a_final = self.artifact(
                f"p2_r{self._rounds}_{self.critic_a_name}", is_json=True
            ).read()
            critic_b_final = self.artifact(
                f"p2_r{self._rounds}_{self.critic_b_name}", is_json=True
            ).read()

            prompt = self.render_template(
                "judge_prompt.md.j2",
                judge_template=judge_template,
                game_plan=game_plan,
                critic_a_name=self.critic_a_name,
                critic_b_name=self.critic_b_name,
                critic_a_final=critic_a_final,
                critic_b_final=critic_b_final,
            )

            response = self.judge.generate(prompt)  # Uses per-model timeout from config
            decision_artifact.write(response)

            # Extract winner
            winner = self._extract_winner(response)
            winner_artifact.path.write_text(f"WINNER={winner}\n")

            console.print(f"  [green]Winner: {winner}[/green]")
        else:
            winner = self.get_winner()
            console.print(f"  [dim]Judge decision (cached) - Winner: {winner}[/dim]")

    def _extract_winner(self, decision: str) -> str:
        """Extract the winner from the judge's decision.

        Args:
            decision: The full judge decision text.

        Returns:
            The winning critic name (e.g., "codex" or "gemini").

        Raises:
            PhaseError: If winner cannot be determined.
        """
        # Build pattern from actual critic names
        critic_names = f"{self.critic_a_name}|{self.critic_b_name}"
        pattern = rf"(?:winner|winning)[^a-z]*({critic_names})"
        match = re.search(pattern, decision, re.IGNORECASE)

        if not match:
            raise PhaseError(
                f"Could not determine winner from judge output. "
                f"Expected one of: {self.critic_a_name}, {self.critic_b_name}. "
                f"Please review: {self.run_dir / 'p3_winner_decision.md'}"
            )

        winner = match.group(1).lower()

        if winner not in (self.critic_a_name, self.critic_b_name):
            raise PhaseError(f"Invalid winner: {winner}")

        return winner

    def get_winner(self) -> str:
        """Get the winner from the winner file.

        Returns:
            The winning critic name (e.g., "codex" or "gemini").

        Raises:
            PhaseError: If winner file doesn't exist or is invalid.
        """
        winner_path = self.run_dir / "p3_winner.txt"
        if not winner_path.exists():
            raise PhaseError("Winner file not found")

        content = winner_path.read_text().strip()
        if content.startswith("WINNER="):
            return content.split("=")[1].strip()

        raise PhaseError(f"Invalid winner file format: {content}")

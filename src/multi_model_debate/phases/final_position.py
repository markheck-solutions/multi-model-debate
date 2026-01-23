"""Phase 6: Strategist generates the Final Position."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from multi_model_debate.exceptions import PhaseError
from multi_model_debate.phases.base import Phase, PhaseArtifact

if TYPE_CHECKING:
    from multi_model_debate.config import Config
    from multi_model_debate.models.protocols import ModelBackend

console = Console()

# Valid status values for issue response checklist
VALID_CHECKLIST_STATUSES = frozenset({"ADDRESSED", "REJECTED", "DEFERRED", "NOT_APPLICABLE"})


@dataclass
class ChecklistItem:
    """An item from the issue response checklist."""

    issue_id: str
    title: str
    response: str
    status: str

    @property
    def is_valid_status(self) -> bool:
        """Check if status is a valid value."""
        return self.status.upper() in VALID_CHECKLIST_STATUSES


@dataclass
class ChecklistCoverage:
    """Coverage statistics for issue response checklist."""

    total: int
    addressed: int
    rejected: int
    deferred: int
    not_applicable: int
    invalid: int

    def summary(self) -> str:
        """Return a human-readable summary of coverage."""
        if self.total == 0:
            return "No checklist items found"
        parts = []
        if self.addressed > 0:
            parts.append(f"{self.addressed} addressed")
        if self.rejected > 0:
            parts.append(f"{self.rejected} rejected")
        if self.deferred > 0:
            parts.append(f"{self.deferred} deferred")
        if self.not_applicable > 0:
            parts.append(f"{self.not_applicable} N/A")
        if self.invalid > 0:
            parts.append(f"{self.invalid} invalid")
        return f"Issue checklist: {', '.join(parts)} (total: {self.total})"


def parse_checklist(content: str) -> list[ChecklistItem]:
    """Parse issue response checklist from Final Position content.

    Looks for markdown table rows with the expected format:
    | Issue ID | Title | Response | Status |

    Args:
        content: The Final Position markdown content.

    Returns:
        List of ChecklistItem objects parsed from the content.
    """
    items: list[ChecklistItem] = []

    # Find the checklist section
    checklist_section = re.search(
        r"##\s*(?:9\.\s*)?ISSUE RESPONSE CHECKLIST(.*?)(?=^##|\Z)",
        content,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not checklist_section:
        return items

    section_content = checklist_section.group(1)

    # Parse markdown table rows (skip header row and separator)
    # Match rows like: | ISSUE-001 | Title | Response | ADDRESSED |
    row_pattern = re.compile(
        r"^\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|?\s*$",
        re.MULTILINE,
    )

    for match in row_pattern.finditer(section_content):
        issue_id, title, response, status = (
            match.group(1).strip(),
            match.group(2).strip(),
            match.group(3).strip(),
            match.group(4).strip(),
        )

        # Skip header row and separator row
        if issue_id.lower() == "issue id" or issue_id.startswith("-"):
            continue
        if all(c in "-: " for c in issue_id):
            continue

        items.append(
            ChecklistItem(
                issue_id=issue_id,
                title=title,
                response=response,
                status=status,
            )
        )

    return items


def calculate_coverage(items: list[ChecklistItem]) -> ChecklistCoverage:
    """Calculate coverage statistics from checklist items.

    Args:
        items: List of ChecklistItem objects.

    Returns:
        ChecklistCoverage with counts for each status.
    """
    addressed = 0
    rejected = 0
    deferred = 0
    not_applicable = 0
    invalid = 0

    for item in items:
        status_upper = item.status.upper()
        if status_upper == "ADDRESSED":
            addressed += 1
        elif status_upper == "REJECTED":
            rejected += 1
        elif status_upper == "DEFERRED":
            deferred += 1
        elif status_upper == "NOT_APPLICABLE":
            not_applicable += 1
        else:
            invalid += 1

    return ChecklistCoverage(
        total=len(items),
        addressed=addressed,
        rejected=rejected,
        deferred=deferred,
        not_applicable=not_applicable,
        invalid=invalid,
    )


class FinalPositionPhase(Phase):
    """Phase 6: Strategist generates the Final Position.

    Fully automated phase where Strategist produces a structured summary with
    recommendations for a non-technical human arbiter to make final decisions.

    DESIGN: Fully automated via CLI calls. Human is notified ONLY at the end
    when the Final Position is ready for review.
    """

    def __init__(
        self,
        run_dir: Path,
        config: Config,
        strategist: ModelBackend,
    ) -> None:
        """Initialize the final position phase.

        Args:
            run_dir: Directory for this run's artifacts.
            config: Configuration settings.
            strategist: Strategist model backend (uses CLI invocation).
        """
        super().__init__(run_dir, config)
        self.strategist = strategist
        self._defense_rounds = config.debate.strategist_rounds

    @property
    def name(self) -> str:
        """Phase identifier."""
        return "PHASE_6"

    @property
    def display_name(self) -> str:
        """Human-readable phase name."""
        return "Final Position"

    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts required for phase completion."""
        return [self.artifact("p6_final_position")]

    def run(self) -> None:
        """Execute the final position phase.

        Strategist generates a comprehensive Final Position with full debate context.
        Fully automated via CLI invocation. Validates issue response checklist.
        """
        final_position_artifact = self.artifact("p6_final_position")

        if not final_position_artifact.is_valid():
            console.print("  [bold cyan]Generating Final Position...[/bold cyan]")

            # Gather all context
            game_plan = self.get_game_plan()
            winner = self._get_winner()
            judge_decision = self.artifact("p3_winner_decision").read()
            peer_review = self.artifact("p4_peer_review").read()
            final_winner = self.artifact(f"p5_r{self._defense_rounds}_winner").read()
            final_strategist = self.artifact(f"p5_r{self._defense_rounds}_strategist").read()

            arbiter_template = self.render_template("arbiter_summary.md.j2")

            prompt = self.render_template(
                "arbiter_prompt.md.j2",
                arbiter_template=arbiter_template,
                game_plan=game_plan,
                winner=winner,
                judge_decision=judge_decision,
                peer_review=peer_review,
                final_winner=final_winner,
                final_strategist=final_strategist,
            )

            # Automated CLI invocation - no more file-based handoff
            response = self.strategist.generate(prompt)  # Uses per-model timeout
            final_position_artifact.write(response)
            # Journal the Strategist response for audit trail
            self.journal_response(round_num=0, response=response)
            console.print("  [green]Final Position complete[/green]")

            # Validate issue response checklist (warn only, don't fail)
            self._validate_checklist(response)
        else:
            console.print("  [dim]Final Position (cached)[/dim]")
            # Also validate checklist on cached content
            self._validate_checklist(final_position_artifact.read())

    def _validate_checklist(self, content: str) -> None:
        """Validate the issue response checklist in Final Position.

        Warns if checklist is missing or incomplete. Does not fail.

        Args:
            content: The Final Position content.
        """
        items = parse_checklist(content)

        if not items:
            console.print(
                "  [yellow]Warning: No issue response checklist found in Final Position.[/yellow]"
            )
            console.print("  [dim]The checklist helps verify all critiques were addressed.[/dim]")
            return

        coverage = calculate_coverage(items)
        console.print(f"  [dim]{coverage.summary()}[/dim]")

        if coverage.invalid > 0:
            console.print(
                f"  [yellow]Warning: {coverage.invalid} checklist item(s) "
                "have invalid status values.[/yellow]"
            )
            console.print(
                "  [dim]Valid statuses: ADDRESSED, REJECTED, DEFERRED, NOT_APPLICABLE[/dim]"
            )

    def _get_winner(self) -> str:
        """Get the winner from Phase 3."""
        winner_path = self.run_dir / "p3_winner.txt"
        if not winner_path.exists():
            raise PhaseError("Winner file not found")
        content = winner_path.read_text().strip()
        if content.startswith("WINNER="):
            return content.split("=")[1].strip()
        raise PhaseError(f"Invalid winner file: {content}")

    def get_final_position(self) -> str:
        """Get the Final Position content.

        Returns:
            The Final Position text.
        """
        return self.artifact("p6_final_position").read()

    def display_final_position(self) -> None:
        """Display the Final Position to the console."""
        final_position = self.get_final_position()
        console.print()
        console.print("=" * 70, style="bold green")
        console.print("  ADVERSARIAL REVIEW COMPLETE", style="bold white")
        console.print("=" * 70, style="bold green")
        console.print()
        console.print(final_position)

"""Base classes for review phases."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from multi_model_debate.response_parser import extract_json_block, is_valid_response

if TYPE_CHECKING:
    from multi_model_debate.config import Config


@dataclass
class PhaseArtifact:
    """Represents a file artifact produced by a phase.

    Used for checkpoint validation - a phase is complete when all
    its required artifacts exist and are valid.

    Attributes:
        name: Artifact identifier.
        path: Path for the artifact file.
        min_length: Minimum content length for non-JSON responses.
        is_json: If True, save JSON cleanly without fences and use .json extension.
    """

    name: str
    path: Path
    min_length: int = 100
    is_json: bool = False

    def exists(self) -> bool:
        """Check if the artifact file exists."""
        return self.path.exists()

    def is_valid(self) -> bool:
        """Check if artifact exists and meets validity criteria.

        Uses JSON-aware validation that accepts:
        - Valid JSON responses (any length)
        - "NO NEW ISSUES" format for convergence
        - Non-JSON responses meeting minimum length

        Returns:
            True if artifact exists and is valid.
        """
        if not self.path.exists():
            return False
        content = self.path.read_text()
        return is_valid_response(content, self.min_length)

    def read(self) -> str:
        """Read the artifact content.

        Returns:
            The artifact file content.

        Raises:
            FileNotFoundError: If artifact doesn't exist.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Artifact not found: {self.path}")
        return self.path.read_text()

    def write(self, content: str) -> None:
        """Write content to the artifact file.

        If is_json=True, extracts clean JSON from markdown fences
        before saving. This ensures artifacts are stored as valid
        JSON files without markdown wrapper.

        Args:
            content: The content to write.
        """
        if self.is_json:
            # Try to extract clean JSON from markdown fences
            json_content = extract_json_block(content)
            if json_content is not None:
                self.path.write_text(json_content)
                return

        # Write content as-is (either not JSON or no fences to strip)
        self.path.write_text(content)


class Phase(ABC):
    """Base class for review phases.

    Each phase represents a stage in the adversarial review workflow.
    Phases produce artifacts (files) that can be validated for checkpoint/resume.
    """

    def __init__(self, run_dir: Path, config: Config) -> None:
        """Initialize the phase.

        Args:
            run_dir: Directory for this run's artifacts.
            config: Configuration settings.
        """
        self.run_dir = run_dir
        self.config = config
        self._template_env: Environment | None = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Phase identifier for checkpointing (e.g., 'PHASE_1')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable phase name for logging."""
        ...

    @abstractmethod
    def required_artifacts(self) -> list[PhaseArtifact]:
        """Artifacts that must exist for phase to be complete.

        Returns:
            List of PhaseArtifact instances.
        """
        ...

    @abstractmethod
    def run(self) -> None:
        """Execute the phase.

        May be partial if resuming - implementations should check
        if individual artifacts already exist before generating them.
        """
        ...

    def is_complete(self) -> bool:
        """Check if all required artifacts are valid.

        Returns:
            True if phase is complete.
        """
        return all(artifact.is_valid() for artifact in self.required_artifacts())

    @property
    def template_env(self) -> Environment:
        """Get the Jinja2 template environment.

        Lazily creates the environment on first access.
        """
        if self._template_env is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
            self._template_env = Environment(
                loader=FileSystemLoader(prompts_dir),
                undefined=StrictUndefined,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return self._template_env

    def render_template(self, template_name: str, **kwargs: object) -> str:
        """Render a Jinja2 template.

        Args:
            template_name: Name of template file (e.g., 'critic_1_lens.md.j2').
            **kwargs: Template variables.

        Returns:
            Rendered template string.
        """
        template = self.template_env.get_template(template_name)
        return template.render(**kwargs)

    def get_game_plan(self) -> str:
        """Read the game plan from the run directory.

        Returns:
            The game plan content.
        """
        return (self.run_dir / "00_game_plan.md").read_text()

    def artifact(
        self,
        name: str,
        filename: str | None = None,
        *,
        is_json: bool = False,
    ) -> PhaseArtifact:
        """Create a PhaseArtifact for this phase.

        Args:
            name: Artifact name.
            filename: File name. If is_json=True, defaults to name + '.json',
                     otherwise defaults to name + '.md'.
            is_json: If True, save as clean JSON with .json extension.

        Returns:
            PhaseArtifact instance.
        """
        if filename is None:
            extension = ".json" if is_json else ".md"
            filename = f"{name}{extension}"

        return PhaseArtifact(
            name=name,
            path=self.run_dir / filename,
            min_length=self.config.models.min_response_length,
            is_json=is_json,
        )

    def journal_response(self, round_num: int, response: str) -> None:
        """Journal a Strategist response for audit trail.

        Appends entry to strategist_journal.jsonl in JSONL format.
        Used by DefensePhase and FinalPositionPhase to record Strategist outputs.

        See REQUIREMENTS_V2.md Section 5 for journaling rationale.

        Args:
            round_num: Round number within the phase (0 for initial/only).
            response: The Strategist's response text.
        """
        journal_path = self.run_dir / "strategist_journal.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": self.name,
            "round": round_num,
            "response_length": len(response),
            "response": response,
        }
        with journal_path.open("a") as f:
            f.write(json.dumps(entry) + "\n")

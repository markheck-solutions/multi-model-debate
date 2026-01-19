"""Run directory management and checkpointing.

This module handles:
- Run directory creation and management
- Checkpointing for resume capability
- Strategist response journaling
- Prompt template hash validation

See REQUIREMENTS_V2.md Section 5 for journaling and hash validation rationale.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from multi_model_debate.config import Config


# Default prompts directory (relative to package)
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Environment variables included in integrity hash
# These affect model detection and role assignment
INTEGRITY_ENV_VARS = (
    "ADVERSARIAL_CRITIQUE_STRATEGIST",
    "ANTHROPIC_MODEL",
    "OPENAI_MODEL",
    "GEMINI_MODEL",
)

# Default config filename
DEFAULT_CONFIG_FILE = "multi_model_debate.toml"


@dataclass
class RunContext:
    """Context for a single review run.

    Manages the run directory, manifest, checkpoints, and status.
    """

    run_dir: Path
    game_plan_path: Path
    config: Config
    manifest: dict[str, Any] = field(default_factory=dict)

    @property
    def checkpoint_file(self) -> Path:
        """Path to the checkpoint file."""
        return self.run_dir / "checkpoint.txt"

    @property
    def status_file(self) -> Path:
        """Path to the status file."""
        return self.run_dir / "status.txt"

    @property
    def manifest_file(self) -> Path:
        """Path to the manifest file."""
        return self.run_dir / "manifest.json"

    @property
    def error_log(self) -> Path:
        """Path to the CLI error log."""
        return self.run_dir / "cli_errors.log"

    @property
    def journal_path(self) -> Path:
        """Path to the Strategist response journal."""
        return self.run_dir / "strategist_journal.jsonl"

    @property
    def integrity_hash_file(self) -> Path:
        """Path to the integrity hash file (prompts + config + env vars)."""
        return self.run_dir / "integrity_hash.txt"

    @property
    def prompt_hash_file(self) -> Path:
        """Path to the legacy prompt hash file (backwards compatibility)."""
        return self.run_dir / "prompt_hash.txt"

    @property
    def pre_debate_file(self) -> Path:
        """Path to the pre-debate completion marker file."""
        return self.run_dir / "pre_debate_complete.txt"

    def is_pre_debate_complete(self) -> bool:
        """Check if the pre-debate protocol has been completed.

        Returns:
            True if pre-debate is marked complete.
        """
        return self.pre_debate_file.exists()

    def mark_pre_debate_complete(self) -> None:
        """Mark the pre-debate protocol as complete."""
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        self.pre_debate_file.write_text(f"PRE_DEBATE_COMPLETE at {timestamp}\n")

    def journal_response(self, phase: str, round_num: int, response: str) -> None:
        """Append a Strategist response to the journal.

        Journals are stored as JSONL (one JSON object per line) for easy parsing.
        See REQUIREMENTS_V2.md Section 5 for journaling rationale.

        Args:
            phase: Phase identifier (e.g., "PHASE_5", "PHASE_6").
            round_num: Round number within the phase (0 for initial).
            response: The Strategist's response text.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "round": round_num,
            "response_length": len(response),
            "response": response,
        }
        with self.journal_path.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def completed_phases(self) -> set[str]:
        """Get the set of completed phase names.

        Returns:
            Set of phase identifiers that have been completed.
        """
        if not self.checkpoint_file.exists():
            return set()
        content = self.checkpoint_file.read_text().strip()
        if not content:
            return set()
        return set(content.split("\n"))

    def mark_complete(self, phase_name: str) -> None:
        """Mark a phase as complete.

        Args:
            phase_name: The phase identifier to mark complete.
        """
        with self.checkpoint_file.open("a") as f:
            f.write(f"{phase_name}\n")

    def log_status(self, message: str) -> None:
        """Log a status message with timestamp.

        Args:
            message: The status message to log.
        """
        timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        with self.status_file.open("a") as f:
            f.write(f"{message} at {timestamp}\n")

    def is_complete(self) -> bool:
        """Check if the run is complete.

        Returns:
            True if the status file contains COMPLETED.
        """
        if not self.status_file.exists():
            return False
        return "COMPLETED" in self.status_file.read_text()


def create_run_from_content(
    content: str,
    runs_dir: Path,
    config: Config,
    source_name: str = "stdin",
) -> RunContext:
    """Create a new run directory from game plan content.

    Args:
        content: The game plan content as a string.
        runs_dir: Directory to create runs in.
        config: Configuration settings.
        source_name: Name to record as the source (for manifest).

    Returns:
        RunContext for the new run.
    """
    # Create timestamped run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True, mode=0o700)

    # Write game plan content
    (run_dir / "00_game_plan.md").write_text(content)

    # Create manifest
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "user": os.environ.get("USER", "unknown"),
        "hostname": os.uname().nodename,
        "working_dir": str(Path.cwd()),
        "script_version": "1.0.0",
        "game_plan": source_name,
        "game_plan_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "config": {
            "critic_rounds": config.debate.critic_rounds,
            "strategist_rounds": config.debate.strategist_rounds,
            "default_timeout": config.models.default_timeout,
            "max_attempts": config.retry.max_attempts,
        },
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # Initialize files
    (run_dir / "checkpoint.txt").touch()
    (run_dir / "cli_errors.log").touch()
    (run_dir / "status.txt").touch()

    # Save integrity hash for resume validation
    save_integrity_hash(run_dir)

    # For stdin, we use a sentinel path that indicates content came from stdin
    game_plan_path = run_dir / "00_game_plan.md"

    context = RunContext(
        run_dir=run_dir,
        game_plan_path=game_plan_path,
        config=config,
        manifest=manifest,
    )
    context.log_status("STARTED")

    return context


def create_run(
    game_plan: Path,
    runs_dir: Path,
    config: Config,
) -> RunContext:
    """Create a new run directory from a game plan file.

    Args:
        game_plan: Path to the game plan file.
        runs_dir: Directory to create runs in.
        config: Configuration settings.

    Returns:
        RunContext for the new run.
    """
    content = game_plan.read_text()
    context = create_run_from_content(
        content=content,
        runs_dir=runs_dir,
        config=config,
        source_name=str(game_plan),
    )
    # Update game_plan_path to point to original file (for integrity checks)
    context.game_plan_path = game_plan
    return context


def find_latest_incomplete_run(runs_dir: Path) -> Path | None:
    """Find the most recent incomplete run directory.

    Args:
        runs_dir: Directory containing run subdirectories.

    Returns:
        Path to the run directory, or None if no incomplete runs.
    """
    if not runs_dir.exists():
        return None

    # Find all run directories (timestamped format)
    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir() and d.name[:2].isdigit()],
        reverse=True,
    )

    for run_dir in run_dirs:
        status_file = run_dir / "status.txt"
        if status_file.exists():
            content = status_file.read_text()
            if "COMPLETED" not in content:
                return run_dir

    return None


def load_run(run_dir: Path, config: Config) -> RunContext:
    """Load an existing run context.

    Args:
        run_dir: Path to the run directory.
        config: Configuration settings.

    Returns:
        RunContext for the existing run.
    """
    manifest_file = run_dir / "manifest.json"
    manifest = {}
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())

    game_plan_path = run_dir / "00_game_plan.md"

    context = RunContext(
        run_dir=run_dir,
        game_plan_path=game_plan_path,
        config=config,
        manifest=manifest,
    )
    context.log_status("RESUMED")

    return context


def verify_game_plan_integrity(context: RunContext) -> bool:
    """Verify the game plan hasn't changed since run started.

    Args:
        context: The run context to verify.

    Returns:
        True if the game plan matches the original hash.
    """
    if "game_plan_sha256" not in context.manifest:
        return True  # No hash to verify

    game_plan_path = context.run_dir / "00_game_plan.md"
    if not game_plan_path.exists():
        return False

    current_hash = hashlib.sha256(game_plan_path.read_bytes()).hexdigest()
    original_hash = str(context.manifest.get("game_plan_sha256", ""))

    return current_hash == original_hash


# =============================================================================
# Integrity Hash Validation
# =============================================================================
# See REQUIREMENTS_V2.md Section 5 for rationale:
# A "Zombie Session" where history was generated with different prompts, config,
# or env vars produces unreliable outputs. We block resume if any of these changed.
# =============================================================================


def compute_integrity_hash(
    prompts_dir: Path | None = None,
    config_file: Path | None = None,
) -> str:
    """Compute SHA-256 hash of prompts, config, and relevant env vars.

    Creates a deterministic hash by:
    1. Hashing all .j2 template files (sorted alphabetically)
    2. Hashing the config file contents
    3. Hashing relevant environment variables (sorted by name)

    Args:
        prompts_dir: Directory containing .j2 template files.
                    Defaults to package prompts directory.
        config_file: Path to config file. Defaults to multi_model_debate.toml
                    in current directory.

    Returns:
        SHA-256 hex digest of all integrity-relevant state.
    """
    if prompts_dir is None:
        prompts_dir = PROMPTS_DIR
    if config_file is None:
        config_file = Path.cwd() / DEFAULT_CONFIG_FILE

    hasher = hashlib.sha256()

    # 1. Hash prompt templates (sorted for deterministic ordering)
    prompt_files = sorted(prompts_dir.glob("*.j2"))
    for prompt_file in prompt_files:
        # Include filename in hash to detect renames
        hasher.update(b"PROMPT:")
        hasher.update(prompt_file.name.encode())
        hasher.update(prompt_file.read_bytes())

    # 2. Hash config file if it exists
    if config_file.exists():
        hasher.update(b"CONFIG:")
        hasher.update(config_file.read_bytes())

    # 3. Hash relevant environment variables (sorted for determinism)
    for var_name in sorted(INTEGRITY_ENV_VARS):
        var_value = os.environ.get(var_name, "")
        hasher.update(b"ENV:")
        hasher.update(var_name.encode())
        hasher.update(b"=")
        hasher.update(var_value.encode())

    return hasher.hexdigest()


def save_integrity_hash(
    run_dir: Path,
    prompts_dir: Path | None = None,
    config_file: Path | None = None,
) -> str:
    """Compute and save integrity hash to run directory.

    Called at debate start to record the state of prompts, config, and env vars.

    Args:
        run_dir: Run directory to save hash in.
        prompts_dir: Directory containing .j2 template files.
        config_file: Path to config file.

    Returns:
        The computed hash.
    """
    integrity_hash = compute_integrity_hash(prompts_dir, config_file)
    (run_dir / "integrity_hash.txt").write_text(integrity_hash)
    return integrity_hash


def validate_integrity_hash(
    run_dir: Path,
    prompts_dir: Path | None = None,
    config_file: Path | None = None,
) -> bool:
    """Check if prompts, config, or env vars have changed since debate started.

    Called on resume to detect modifications that would invalidate the debate.

    Args:
        run_dir: Run directory containing stored hash.
        prompts_dir: Directory containing .j2 template files.
        config_file: Path to config file.

    Returns:
        True if everything matches (safe to resume), False if changed.
    """
    # Check new integrity hash file first
    integrity_hash_file = run_dir / "integrity_hash.txt"
    if integrity_hash_file.exists():
        stored_hash = integrity_hash_file.read_text().strip()
        current_hash = compute_integrity_hash(prompts_dir, config_file)
        return stored_hash == current_hash

    # Fall back to legacy prompt_hash.txt for backwards compatibility
    legacy_hash_file = run_dir / "prompt_hash.txt"
    if legacy_hash_file.exists():
        # Legacy runs only checked prompts, so only validate prompts
        stored_hash = legacy_hash_file.read_text().strip()
        current_hash = compute_prompt_hash(prompts_dir)
        return stored_hash == current_hash

    # No hash stored - assume safe (very old runs)
    return True


# Legacy function for backwards compatibility with existing tests
def compute_prompt_hash(prompts_dir: Path | None = None) -> str:
    """Compute SHA-256 hash of prompt templates only.

    This is a legacy function for backwards compatibility.
    New code should use compute_integrity_hash().

    Args:
        prompts_dir: Directory containing .j2 template files.

    Returns:
        SHA-256 hex digest of prompt templates.
    """
    if prompts_dir is None:
        prompts_dir = PROMPTS_DIR

    hasher = hashlib.sha256()
    prompt_files = sorted(prompts_dir.glob("*.j2"))

    for prompt_file in prompt_files:
        hasher.update(prompt_file.name.encode())
        hasher.update(prompt_file.read_bytes())

    return hasher.hexdigest()


# Legacy functions for backwards compatibility
def save_prompt_hash(run_dir: Path, prompts_dir: Path | None = None) -> str:
    """Legacy function - use save_integrity_hash() instead."""
    return save_integrity_hash(run_dir, prompts_dir)


def validate_prompt_hash(run_dir: Path, prompts_dir: Path | None = None) -> bool:
    """Legacy function - use validate_integrity_hash() instead."""
    return validate_integrity_hash(run_dir, prompts_dir)


class PromptHashMismatchError(Exception):
    """Raised when integrity validation fails.

    This is a blocking error - the debate must be restarted.
    See REQUIREMENTS_V2.md Section 5 for rationale.
    """

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        super().__init__(
            "Integrity check failed: prompts, config, or environment have changed.\n"
            "A debate with changed state produces unreliable results.\n"
            "Must restart debate from beginning."
        )

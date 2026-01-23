"""Tests for storage and run management."""

import json
import os
from pathlib import Path
from unittest.mock import patch

from multi_model_debate.config import Config
from multi_model_debate.storage.run import (
    INTEGRITY_ENV_VARS,
    PromptHashMismatchError,
    RunContext,
    compute_integrity_hash,
    compute_prompt_hash,
    create_run,
    find_latest_incomplete_run,
    save_integrity_hash,
    save_prompt_hash,
    validate_integrity_hash,
    validate_prompt_hash,
    verify_game_plan_integrity,
)


class TestRunContext:
    """Tests for RunContext dataclass."""

    def test_checkpoint_file_path(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test checkpoint file path."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert context.checkpoint_file == tmp_run_dir / "checkpoint.txt"

    def test_status_file_path(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test status file path."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert context.status_file == tmp_run_dir / "status.txt"

    def test_completed_phases_empty(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test completed phases when file doesn't exist."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert context.completed_phases() == set()

    def test_completed_phases_with_content(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test completed phases with content."""
        (tmp_run_dir / "checkpoint.txt").write_text("PHASE_1\nPHASE_2\n")

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert context.completed_phases() == {"PHASE_1", "PHASE_2"}

    def test_mark_complete(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test marking a phase complete."""
        (tmp_run_dir / "checkpoint.txt").touch()

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        context.mark_complete("PHASE_1")

        content = (tmp_run_dir / "checkpoint.txt").read_text()
        assert "PHASE_1" in content

    def test_log_status(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test logging status."""
        (tmp_run_dir / "status.txt").touch()

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        context.log_status("STARTED")

        content = (tmp_run_dir / "status.txt").read_text()
        assert "STARTED" in content

    def test_is_complete_false(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test is_complete when not complete."""
        (tmp_run_dir / "status.txt").write_text("STARTED at ...\n")

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert not context.is_complete()

    def test_is_complete_true(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test is_complete when complete."""
        (tmp_run_dir / "status.txt").write_text("COMPLETED at ...\n")

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert context.is_complete()


class TestCreateRun:
    """Tests for create_run function."""

    def test_creates_run_directory(
        self, tmp_path: Path, sample_game_plan: Path, default_config: Config
    ) -> None:
        """Test that run directory is created."""
        runs_dir = tmp_path / "runs"

        context = create_run(sample_game_plan, runs_dir, default_config)

        assert context.run_dir.exists()
        assert context.run_dir.parent == runs_dir

    def test_copies_game_plan(
        self, tmp_path: Path, sample_game_plan: Path, default_config: Config
    ) -> None:
        """Test that game plan is copied."""
        runs_dir = tmp_path / "runs"

        context = create_run(sample_game_plan, runs_dir, default_config)

        copied_plan = context.run_dir / "00_game_plan.md"
        assert copied_plan.exists()
        assert copied_plan.read_text() == sample_game_plan.read_text()

    def test_creates_manifest(
        self, tmp_path: Path, sample_game_plan: Path, default_config: Config
    ) -> None:
        """Test that manifest is created."""
        runs_dir = tmp_path / "runs"

        context = create_run(sample_game_plan, runs_dir, default_config)

        manifest_file = context.run_dir / "manifest.json"
        assert manifest_file.exists()

    def test_creates_checkpoint_file(
        self, tmp_path: Path, sample_game_plan: Path, default_config: Config
    ) -> None:
        """Test that checkpoint file is created."""
        runs_dir = tmp_path / "runs"

        context = create_run(sample_game_plan, runs_dir, default_config)

        assert context.checkpoint_file.exists()


class TestFindLatestIncompleteRun:
    """Tests for find_latest_incomplete_run function."""

    def test_returns_none_when_no_runs(self, tmp_path: Path) -> None:
        """Test returns None when runs directory doesn't exist."""
        runs_dir = tmp_path / "runs"
        assert find_latest_incomplete_run(runs_dir) is None

    def test_returns_none_when_all_complete(self, tmp_path: Path) -> None:
        """Test returns None when all runs are complete."""
        runs_dir = tmp_path / "runs"
        run_dir = runs_dir / "20260101_120000"
        run_dir.mkdir(parents=True)
        (run_dir / "status.txt").write_text("COMPLETED at ...\n")

        assert find_latest_incomplete_run(runs_dir) is None

    def test_returns_incomplete_run(self, tmp_path: Path) -> None:
        """Test returns incomplete run."""
        runs_dir = tmp_path / "runs"
        run_dir = runs_dir / "20260101_120000"
        run_dir.mkdir(parents=True)
        (run_dir / "status.txt").write_text("STARTED at ...\n")

        result = find_latest_incomplete_run(runs_dir)
        assert result == run_dir


class TestVerifyGamePlanIntegrity:
    """Tests for verify_game_plan_integrity function."""

    def test_returns_true_when_no_hash(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test returns True when no hash in manifest."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
            manifest={},
        )

        assert verify_game_plan_integrity(context) is True

    def test_returns_true_when_hash_matches(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test returns True when hash matches."""
        import hashlib

        game_plan_content = "# Game Plan\nContent here."
        (tmp_run_dir / "00_game_plan.md").write_text(game_plan_content)
        expected_hash = hashlib.sha256(game_plan_content.encode()).hexdigest()

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "00_game_plan.md",
            config=default_config,
            manifest={"game_plan_sha256": expected_hash},
        )

        assert verify_game_plan_integrity(context) is True

    def test_returns_false_when_hash_differs(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test returns False when hash differs."""
        (tmp_run_dir / "00_game_plan.md").write_text("Modified content")

        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "00_game_plan.md",
            config=default_config,
            manifest={"game_plan_sha256": "different_hash"},
        )

        assert verify_game_plan_integrity(context) is False


class TestJournaling:
    """Tests for Strategist response journaling."""

    def test_journal_response_creates_file(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test journaling creates the journal file."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        context.journal_response("PHASE_5", 0, "Initial defense response")

        assert context.journal_path.exists()

    def test_journal_response_appends_entry(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test journaling appends entries in JSONL format."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        context.journal_response("PHASE_5", 0, "First response")
        context.journal_response("PHASE_5", 1, "Second response")

        lines = context.journal_path.read_text().strip().split("\n")
        assert len(lines) == 2

        entry1 = json.loads(lines[0])
        assert entry1["phase"] == "PHASE_5"
        assert entry1["round"] == 0
        assert entry1["response"] == "First response"
        assert "timestamp" in entry1
        assert entry1["response_length"] == len("First response")

        entry2 = json.loads(lines[1])
        assert entry2["round"] == 1

    def test_journal_path_property(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test journal_path property returns correct path."""
        context = RunContext(
            run_dir=tmp_run_dir,
            game_plan_path=tmp_run_dir / "game_plan.md",
            config=default_config,
        )

        assert context.journal_path == tmp_run_dir / "strategist_journal.jsonl"


class TestPromptHashValidation:
    """Tests for prompt template hash validation."""

    def test_compute_prompt_hash_deterministic(self, tmp_path: Path) -> None:
        """Test hash computation is deterministic."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("template content")

        hash1 = compute_prompt_hash(prompts_dir)
        hash2 = compute_prompt_hash(prompts_dir)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest

    def test_compute_prompt_hash_changes_on_content_change(self, tmp_path: Path) -> None:
        """Test hash changes when content changes."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("original content")

        hash1 = compute_prompt_hash(prompts_dir)

        (prompts_dir / "test.j2").write_text("modified content")
        hash2 = compute_prompt_hash(prompts_dir)

        assert hash1 != hash2

    def test_compute_prompt_hash_changes_on_new_file(self, tmp_path: Path) -> None:
        """Test hash changes when a new file is added."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test1.j2").write_text("content1")

        hash1 = compute_prompt_hash(prompts_dir)

        (prompts_dir / "test2.j2").write_text("content2")
        hash2 = compute_prompt_hash(prompts_dir)

        assert hash1 != hash2

    def test_compute_prompt_hash_changes_on_rename(self, tmp_path: Path) -> None:
        """Test hash changes when a file is renamed."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "original.j2").write_text("content")

        hash1 = compute_prompt_hash(prompts_dir)

        (prompts_dir / "original.j2").rename(prompts_dir / "renamed.j2")
        hash2 = compute_prompt_hash(prompts_dir)

        assert hash1 != hash2

    def test_save_prompt_hash(self, tmp_path: Path) -> None:
        """Test saving prompt hash to file (legacy wrapper now saves to integrity_hash.txt)."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        saved_hash = save_prompt_hash(run_dir, prompts_dir)
        # Legacy wrapper now calls save_integrity_hash, which writes to integrity_hash.txt
        hash_file = run_dir / "integrity_hash.txt"

        assert hash_file.exists()
        assert hash_file.read_text() == saved_hash

    def test_validate_prompt_hash_returns_true_when_unchanged(self, tmp_path: Path) -> None:
        """Test validation returns True when prompts unchanged."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        save_prompt_hash(run_dir, prompts_dir)

        assert validate_prompt_hash(run_dir, prompts_dir) is True

    def test_validate_prompt_hash_returns_false_when_changed(self, tmp_path: Path) -> None:
        """Test validation returns False when prompts changed."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("original content")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        save_prompt_hash(run_dir, prompts_dir)

        # Modify the prompt
        (prompts_dir / "test.j2").write_text("modified content")

        assert validate_prompt_hash(run_dir, prompts_dir) is False

    def test_validate_prompt_hash_returns_true_when_no_hash_file(self, tmp_path: Path) -> None:
        """Test validation returns True when no hash file (backwards compat)."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        # No hash file saved
        assert validate_prompt_hash(run_dir, prompts_dir) is True


class TestPromptHashMismatchError:
    """Tests for PromptHashMismatchError exception."""

    def test_error_message(self, tmp_path: Path) -> None:
        """Test error has proper message."""
        run_dir = tmp_path / "run"
        error = PromptHashMismatchError(run_dir)

        assert "Integrity check failed" in str(error)
        assert "unreliable results" in str(error)
        assert "restart" in str(error)

    def test_error_stores_run_dir(self, tmp_path: Path) -> None:
        """Test error stores run_dir for reference."""
        run_dir = tmp_path / "run"
        error = PromptHashMismatchError(run_dir)

        assert error.run_dir == run_dir


class TestCreateRunWithPromptHash:
    """Tests for create_run saving integrity hash."""

    def test_creates_integrity_hash_file(
        self, tmp_path: Path, sample_game_plan: Path, default_config: Config
    ) -> None:
        """Test that create_run saves integrity hash."""
        runs_dir = tmp_path / "runs"

        context = create_run(sample_game_plan, runs_dir, default_config)

        hash_file = context.run_dir / "integrity_hash.txt"
        assert hash_file.exists()
        assert len(hash_file.read_text()) == 64  # SHA-256 hex digest


class TestIntegrityHash:
    """Tests for expanded integrity hash (prompts + config + env vars)."""

    def test_compute_integrity_hash_includes_prompts(self, tmp_path: Path) -> None:
        """Test that integrity hash includes prompt templates."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("template content")

        hash1 = compute_integrity_hash(prompts_dir, tmp_path / "nonexistent.toml")

        # Change prompt content
        (prompts_dir / "test.j2").write_text("modified content")
        hash2 = compute_integrity_hash(prompts_dir, tmp_path / "nonexistent.toml")

        assert hash1 != hash2

    def test_compute_integrity_hash_includes_config(self, tmp_path: Path) -> None:
        """Test that integrity hash includes config file."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("template content")

        config_file = tmp_path / "config.toml"
        config_file.write_text("[debate]\nrounds = 4")

        hash1 = compute_integrity_hash(prompts_dir, config_file)

        # Change config
        config_file.write_text("[debate]\nrounds = 6")
        hash2 = compute_integrity_hash(prompts_dir, config_file)

        assert hash1 != hash2

    def test_compute_integrity_hash_includes_env_vars(self, tmp_path: Path) -> None:
        """Test that integrity hash includes environment variables."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("template content")

        # Clear any existing env vars that affect hash
        clean_env = {k: v for k, v in os.environ.items() if k not in INTEGRITY_ENV_VARS}

        with patch.dict(os.environ, clean_env, clear=True):
            hash1 = compute_integrity_hash(prompts_dir, tmp_path / "nonexistent.toml")

            # Set an env var
            os.environ["ANTHROPIC_MODEL"] = "claude-3-opus"
            hash2 = compute_integrity_hash(prompts_dir, tmp_path / "nonexistent.toml")

        assert hash1 != hash2

    def test_compute_integrity_hash_deterministic(self, tmp_path: Path) -> None:
        """Test that integrity hash is deterministic."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        config_file = tmp_path / "config.toml"
        config_file.write_text("[debate]\nrounds = 4")

        hash1 = compute_integrity_hash(prompts_dir, config_file)
        hash2 = compute_integrity_hash(prompts_dir, config_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256

    def test_save_integrity_hash(self, tmp_path: Path) -> None:
        """Test saving integrity hash to file."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        saved_hash = save_integrity_hash(run_dir, prompts_dir)
        hash_file = run_dir / "integrity_hash.txt"

        assert hash_file.exists()
        assert hash_file.read_text() == saved_hash

    def test_validate_integrity_hash_returns_true_when_unchanged(self, tmp_path: Path) -> None:
        """Test validation returns True when nothing changed."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        config_file = tmp_path / "config.toml"
        config_file.write_text("[debate]\nrounds = 4")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        save_integrity_hash(run_dir, prompts_dir, config_file)

        assert validate_integrity_hash(run_dir, prompts_dir, config_file) is True

    def test_validate_integrity_hash_returns_false_when_config_changed(
        self, tmp_path: Path
    ) -> None:
        """Test validation returns False when config changed."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        config_file = tmp_path / "config.toml"
        config_file.write_text("[debate]\nrounds = 4")

        run_dir = tmp_path / "run"
        run_dir.mkdir()
        save_integrity_hash(run_dir, prompts_dir, config_file)

        # Change config
        config_file.write_text("[debate]\nrounds = 8")

        assert validate_integrity_hash(run_dir, prompts_dir, config_file) is False

    def test_validate_integrity_hash_falls_back_to_legacy(self, tmp_path: Path) -> None:
        """Test validation falls back to legacy prompt_hash.txt."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.j2").write_text("content")

        run_dir = tmp_path / "run"
        run_dir.mkdir()

        # Create legacy hash file (prompts only)
        legacy_hash = compute_prompt_hash(prompts_dir)
        (run_dir / "prompt_hash.txt").write_text(legacy_hash)

        # Should validate using legacy prompt-only hash
        assert validate_integrity_hash(run_dir, prompts_dir) is True

        # Change prompts - should fail even with legacy
        (prompts_dir / "test.j2").write_text("modified")
        assert validate_integrity_hash(run_dir, prompts_dir) is False

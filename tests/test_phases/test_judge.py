"""Tests for Phase 3: Winner determination."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from multi_model_debate.config import Config
from multi_model_debate.exceptions import PhaseError
from multi_model_debate.phases.judge import JudgePhase


class TestJudgePhase:
    """Tests for JudgePhase."""

    def test_phase_name(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test phase identifier."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        assert phase.name == "PHASE_3"
        assert phase.display_name == "Winner Determination"

    def test_required_artifacts(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test required artifacts for phase completion."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        artifacts = phase.required_artifacts()
        names = [a.name for a in artifacts]

        assert "p3_winner_decision" in names
        assert "p3_winner" in names

    def test_extract_winner_critic_a(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test extracting first critic as winner."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        decision = """WINNER: codex

REASONING:
codex raised more concrete issues.
"""
        winner = phase._extract_winner(decision)
        assert winner == "codex"

    def test_extract_winner_critic_b(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test extracting second critic as winner."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        decision = """WINNER: GEMINI

REASONING:
Gemini had better arguments.
"""
        winner = phase._extract_winner(decision)
        assert winner == "gemini"

    def test_extract_winner_case_insensitive(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test that winner extraction is case insensitive."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        decision = "WINNER: CODEX"
        winner = phase._extract_winner(decision)
        assert winner == "codex"

    def test_extract_winner_raises_on_invalid(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test that invalid winner raises PhaseError."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        with pytest.raises(PhaseError):
            phase._extract_winner("No clear winner here.")

    def test_get_winner_reads_file(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test getting winner from file."""
        (tmp_run_dir / "p3_winner.txt").write_text("WINNER=gemini\n")

        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        assert phase.get_winner() == "gemini"

    def test_get_winner_raises_when_missing(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test that missing winner file raises PhaseError."""
        phase = JudgePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            judge=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        with pytest.raises(PhaseError):
            phase.get_winner()

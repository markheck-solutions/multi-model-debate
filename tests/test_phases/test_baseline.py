"""Tests for Phase 1: Baseline critiques."""

from pathlib import Path
from unittest.mock import MagicMock

from multi_model_debate.config import Config
from multi_model_debate.phases.baseline import BaselinePhase


class TestBaselinePhase:
    """Tests for BaselinePhase."""

    def test_phase_name(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test phase identifier."""
        phase = BaselinePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            critic_a=MagicMock(),
            critic_b=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        assert phase.name == "PHASE_1"
        assert phase.display_name == "Baseline Critiques"

    def test_required_artifacts(self, tmp_run_dir: Path, default_config: Config) -> None:
        """Test required artifacts for phase completion."""
        phase = BaselinePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            critic_a=MagicMock(),
            critic_b=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        artifacts = phase.required_artifacts()
        names = [a.name for a in artifacts]

        assert "p1_codex_baseline" in names
        assert "p1_gemini_baseline" in names

    def test_is_complete_false_when_no_artifacts(
        self, tmp_run_dir: Path, default_config: Config
    ) -> None:
        """Test phase is incomplete without artifacts."""
        phase = BaselinePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            critic_a=MagicMock(),
            critic_b=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        assert not phase.is_complete()

    def test_is_complete_true_when_json_artifacts_exist(
        self,
        tmp_run_dir: Path,
        default_config: Config,
    ) -> None:
        """Test phase is complete when JSON artifacts exist and are valid."""
        # Create valid artifact files with dynamic names
        (tmp_run_dir / "p1_codex_baseline.json").write_text("x" * 150)
        (tmp_run_dir / "p1_gemini_baseline.json").write_text("y" * 150)

        phase = BaselinePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            critic_a=MagicMock(),
            critic_b=MagicMock(),
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        assert phase.is_complete()

    def test_run_generates_artifacts(
        self,
        tmp_run_dir: Path,
        default_config: Config,
        mock_critic_a: MagicMock,
        mock_critic_b: MagicMock,
    ) -> None:
        """Test running phase generates both baseline artifacts."""
        # Create game plan
        (tmp_run_dir / "00_game_plan.md").write_text("# Test Game Plan\n\nContent here.")

        phase = BaselinePhase(
            run_dir=tmp_run_dir,
            config=default_config,
            critic_a=mock_critic_a,
            critic_b=mock_critic_b,
            critic_a_name="codex",
            critic_b_name="gemini",
        )

        phase.run()

        # Check files were created with dynamic names
        assert (tmp_run_dir / "p1_codex_baseline.json").exists()
        assert (tmp_run_dir / "p1_gemini_baseline.json").exists()

        # Check models were called
        mock_critic_a.generate.assert_called_once()
        mock_critic_b.generate.assert_called_once()

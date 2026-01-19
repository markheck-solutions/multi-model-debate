"""Tests for CLI interface."""

from typer.testing import CliRunner

from multi_model_debate import __version__
from multi_model_debate.cli import app

runner = CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "multi-model-debate" in result.stdout
        assert __version__ in result.stdout

    def test_help(self) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "start" in result.stdout
        assert "resume" in result.stdout
        assert "status" in result.stdout

    def test_start_help(self) -> None:
        """Test start --help."""
        result = runner.invoke(app, ["start", "--help"])

        assert result.exit_code == 0
        assert "game plan" in result.stdout.lower()

    def test_resume_help(self) -> None:
        """Test resume --help."""
        result = runner.invoke(app, ["resume", "--help"])

        assert result.exit_code == 0
        assert "Resume" in result.stdout

    def test_status_no_runs(self, tmp_path) -> None:
        """Test status when no runs exist."""
        result = runner.invoke(app, ["status", "--runs-dir", str(tmp_path / "runs")])

        assert result.exit_code == 0
        assert "No runs found" in result.stdout

    def test_start_missing_file(self, tmp_path) -> None:
        """Test start with missing game plan file."""
        result = runner.invoke(
            app, ["start", str(tmp_path / "nonexistent.md"), "--runs-dir", str(tmp_path)]
        )

        assert result.exit_code != 0

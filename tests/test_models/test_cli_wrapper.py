"""Tests for CLI model wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from multi_model_debate.config import CLICommandConfig, RetrySettings
from multi_model_debate.exceptions import ModelError, ModelValidationError
from multi_model_debate.models.cli_wrapper import CLIModelBackend


class TestCLIModelBackend:
    """Tests for CLIModelBackend."""

    @pytest.fixture
    def cli_config(self) -> CLICommandConfig:
        """Create a test CLI config."""
        return CLICommandConfig(
            command="echo",
            input_mode="positional",
        )

    @pytest.fixture
    def retry_config(self) -> RetrySettings:
        """Create a test retry config."""
        return RetrySettings(max_attempts=2, base_delay=1)

    def test_name_property(self, cli_config: CLICommandConfig, retry_config: RetrySettings) -> None:
        """Test name property."""
        backend = CLIModelBackend(
            name="TestModel",
            cli_config=cli_config,
            retry_config=retry_config,
        )

        assert backend.name == "TestModel"

    def test_build_command_positional(self) -> None:
        """Test building command with positional input."""
        config = CLICommandConfig(command="mycommand", input_mode="positional")
        retry = RetrySettings(max_attempts=1, base_delay=1)
        backend = CLIModelBackend("Test", config, retry)

        cmd = backend._build_command("hello world")

        assert cmd == ["mycommand", "hello world"]

    def test_build_command_stdin(self) -> None:
        """Test building command with stdin input."""
        config = CLICommandConfig(
            command="mycommand",
            subcommand="exec",
            input_mode="stdin",
        )
        retry = RetrySettings(max_attempts=1, base_delay=1)
        backend = CLIModelBackend("Test", config, retry)

        cmd = backend._build_command("hello world")

        assert cmd == ["mycommand", "exec", "-"]

    def test_build_command_with_flags(self) -> None:
        """Test building command with flags."""
        config = CLICommandConfig(
            command="mycommand",
            flags=["--verbose", "-n", "5"],
            input_mode="positional",
        )
        retry = RetrySettings(max_attempts=1, base_delay=1)
        backend = CLIModelBackend("Test", config, retry)

        cmd = backend._build_command("prompt")

        assert cmd == ["mycommand", "--verbose", "-n", "5", "prompt"]

    def test_validate_response_empty_raises_error(
        self, cli_config: CLICommandConfig, retry_config: RetrySettings
    ) -> None:
        """Test that empty response raises error."""
        backend = CLIModelBackend("Test", cli_config, retry_config)

        with pytest.raises(ModelValidationError):
            backend._validate_response("")

    def test_validate_response_too_short_raises_error(
        self, cli_config: CLICommandConfig, retry_config: RetrySettings
    ) -> None:
        """Test that too-short response raises error."""
        backend = CLIModelBackend("Test", cli_config, retry_config, min_response_length=100)

        with pytest.raises(ModelValidationError):
            backend._validate_response("short response")

    def test_validate_response_allows_no_new_issues(
        self, cli_config: CLICommandConfig, retry_config: RetrySettings
    ) -> None:
        """Test that 'NO NEW ISSUES' is allowed even if short."""
        backend = CLIModelBackend("Test", cli_config, retry_config, min_response_length=100)

        # Should not raise
        backend._validate_response("NO NEW ISSUES. Previous critiques cover concerns.")

    @patch("subprocess.run")
    def test_generate_success(
        self,
        mock_run: MagicMock,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
    ) -> None:
        """Test successful generation."""
        mock_run.return_value = MagicMock(
            stdout="This is a valid response that is long enough to pass validation.",
            stderr="",
            returncode=0,
        )

        backend = CLIModelBackend("Test", cli_config, retry_config, min_response_length=50)

        result = backend.generate("test prompt")

        assert "valid response" in result
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_generate_retries_on_failure(
        self,
        mock_run: MagicMock,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
    ) -> None:
        """Test that generation retries on failure."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            MagicMock(stdout="", stderr="error", returncode=1),
            MagicMock(
                stdout="Valid response after retry with enough content.",
                stderr="",
                returncode=0,
            ),
        ]

        backend = CLIModelBackend("Test", cli_config, retry_config, min_response_length=30)

        result = backend.generate("test prompt")

        assert "Valid response" in result
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_generate_raises_after_max_retries(
        self,
        mock_run: MagicMock,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
    ) -> None:
        """Test that generation raises error after max retries."""
        mock_run.return_value = MagicMock(stdout="", stderr="error", returncode=1)

        backend = CLIModelBackend("Test", cli_config, retry_config)

        with pytest.raises(ModelError, match="failed after 2 attempts"):
            backend.generate("test prompt")

        assert mock_run.call_count == 2

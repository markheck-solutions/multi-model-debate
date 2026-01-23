"""Claude CLI model backend with Strategist support."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from multi_model_debate.models.cli_wrapper import CLIModelBackend

if TYPE_CHECKING:
    from multi_model_debate.config import CLICommandConfig, RetrySettings

console = Console()


class ClaudeBackend(CLIModelBackend):
    """Claude CLI backend for non-interactive invocations.

    Used for Phase 3 (judge) where Claude makes a one-shot determination.
    """

    def __init__(
        self,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
        min_response_length: int = 100,
        error_log: Path | None = None,
    ) -> None:
        """Initialize the Claude backend.

        Args:
            cli_config: CLI command configuration.
            retry_config: Retry settings for exponential backoff.
            min_response_length: Minimum chars for valid response.
            error_log: Optional path to log stderr output.
        """
        super().__init__(
            name="Claude",
            cli_config=cli_config,
            retry_config=retry_config,
            min_response_length=min_response_length,
            error_log=error_log,
        )


class StrategistBackend(CLIModelBackend):
    """CLI-based backend for Strategist in Phases 5-6.

    The Strategist is the AI assistant with full context that authored the
    game plan. It defends the proposal automatically using CLI invocation,
    just like other model backends.

    DESIGN: Fully automated via CLI calls, same as other model backends.
    """

    def __init__(
        self,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
        min_response_length: int = 100,
        error_log: Path | None = None,
        default_timeout: int = 300,
    ) -> None:
        """Initialize the Strategist backend.

        Args:
            cli_config: CLI command configuration (uses claude CLI).
            retry_config: Retry settings for exponential backoff.
            min_response_length: Minimum chars for valid response.
            error_log: Optional path to log stderr output.
            default_timeout: Default timeout if not specified in cli_config.
        """
        super().__init__(
            name="Strategist",
            cli_config=cli_config,
            retry_config=retry_config,
            min_response_length=min_response_length,
            error_log=error_log,
            default_timeout=default_timeout,
        )


def create_claude_backend(
    cli_config: CLICommandConfig,
    retry_config: RetrySettings,
    min_response_length: int = 100,
    error_log: Path | None = None,
) -> ClaudeBackend:
    """Factory function to create a non-interactive Claude backend.

    Args:
        cli_config: CLI command configuration.
        retry_config: Retry settings.
        min_response_length: Minimum response length.
        error_log: Optional error log path.

    Returns:
        Configured ClaudeBackend instance.
    """
    return ClaudeBackend(
        cli_config=cli_config,
        retry_config=retry_config,
        min_response_length=min_response_length,
        error_log=error_log,
    )


def create_strategist_backend(
    cli_config: CLICommandConfig,
    retry_config: RetrySettings,
    min_response_length: int = 100,
    error_log: Path | None = None,
    default_timeout: int = 300,
) -> StrategistBackend:
    """Factory function to create a Strategist backend.

    The Strategist uses the configured CLI for automated responses.
    See REQUIREMENTS_V2.md Section 4 for rationale on full automation.

    Args:
        cli_config: CLI command configuration.
        retry_config: Retry settings for exponential backoff.
        min_response_length: Minimum response length.
        error_log: Optional error log path.
        default_timeout: Default timeout if not specified in cli_config.

    Returns:
        Configured StrategistBackend instance.
    """
    return StrategistBackend(
        cli_config=cli_config,
        retry_config=retry_config,
        min_response_length=min_response_length,
        error_log=error_log,
        default_timeout=default_timeout,
    )


# Backwards compatibility alias (deprecated)
def create_claude_interactive_backend(
    min_response_length: int = 100,
) -> StrategistBackend:
    """Deprecated: Use create_strategist_backend instead.

    This function is kept for backwards compatibility but will be removed.
    It creates a StrategistBackend with default CLI config.
    """
    import warnings

    from multi_model_debate.config import CLICommandConfig, RetrySettings

    warnings.warn(
        "create_claude_interactive_backend is deprecated, use create_strategist_backend",
        DeprecationWarning,
        stacklevel=2,
    )
    # Create with defaults - caller should use create_strategist_backend instead
    default_cli = CLICommandConfig(
        command="claude", input_mode="positional", flags=["-p", "--tools", "", "--"]
    )
    default_retry = RetrySettings(max_attempts=3, base_delay=30)
    return StrategistBackend(
        cli_config=default_cli,
        retry_config=default_retry,
        min_response_length=min_response_length,
    )

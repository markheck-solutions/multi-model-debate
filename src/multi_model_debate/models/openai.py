"""OpenAI/Codex CLI model backend."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from multi_model_debate.models.cli_wrapper import CLIModelBackend

if TYPE_CHECKING:
    from multi_model_debate.config import CLICommandConfig, RetrySettings


class CodexBackend(CLIModelBackend):
    """Codex CLI backend for GPT model invocations.

    Wraps the `codex exec -` command which reads prompts from stdin.
    """

    def __init__(
        self,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
        min_response_length: int = 100,
        error_log: Path | None = None,
    ) -> None:
        """Initialize the Codex backend.

        Args:
            cli_config: CLI command configuration (typically codex exec).
            retry_config: Retry settings for exponential backoff.
            min_response_length: Minimum chars for valid response.
            error_log: Optional path to log stderr output.
        """
        super().__init__(
            name="GPT",
            cli_config=cli_config,
            retry_config=retry_config,
            min_response_length=min_response_length,
            error_log=error_log,
        )


def create_codex_backend(
    cli_config: CLICommandConfig,
    retry_config: RetrySettings,
    min_response_length: int = 100,
    error_log: Path | None = None,
) -> CodexBackend:
    """Factory function to create a Codex backend.

    Args:
        cli_config: CLI command configuration.
        retry_config: Retry settings.
        min_response_length: Minimum response length.
        error_log: Optional error log path.

    Returns:
        Configured CodexBackend instance.
    """
    return CodexBackend(
        cli_config=cli_config,
        retry_config=retry_config,
        min_response_length=min_response_length,
        error_log=error_log,
    )

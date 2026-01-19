"""Model backends for CLI-based AI model invocations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from multi_model_debate.models.claude import (
    ClaudeBackend,
    StrategistBackend,
    create_claude_backend,
    create_claude_interactive_backend,  # Deprecated, kept for backwards compat
    create_strategist_backend,
)
from multi_model_debate.models.cli_wrapper import CLIModelBackend
from multi_model_debate.models.gemini import GeminiBackend, create_gemini_backend
from multi_model_debate.models.openai import CodexBackend, create_codex_backend
from multi_model_debate.models.protocols import ModelBackend

if TYPE_CHECKING:
    from multi_model_debate.config import CLICommandConfig, RetrySettings


def create_cli_backend(
    name: str,
    cli_config: CLICommandConfig,
    retry_config: RetrySettings,
    min_response_length: int = 100,
    default_timeout: int = 300,
) -> CLIModelBackend:
    """Create a CLI model backend for any model.

    This is a generic factory that works with any CLI-based model.
    Use this for dynamic model loading from config.

    Args:
        name: Human-readable model name (e.g., 'GPT', 'Gemini', 'Claude').
        cli_config: CLI command configuration from config.
        retry_config: Retry settings for exponential backoff.
        min_response_length: Minimum chars for valid response.
        default_timeout: Global default timeout (per-model config takes priority).

    Returns:
        A CLIModelBackend instance configured for the model.
    """
    return CLIModelBackend(
        name=name.upper(),
        cli_config=cli_config,
        retry_config=retry_config,
        min_response_length=min_response_length,
        default_timeout=default_timeout,
    )


__all__ = [
    # Protocols
    "ModelBackend",
    # Base
    "CLIModelBackend",
    # Implementations
    "CodexBackend",
    "GeminiBackend",
    "ClaudeBackend",
    "StrategistBackend",
    # Factories
    "create_cli_backend",
    "create_codex_backend",
    "create_gemini_backend",
    "create_claude_backend",
    "create_strategist_backend",
    "create_claude_interactive_backend",  # Deprecated
]

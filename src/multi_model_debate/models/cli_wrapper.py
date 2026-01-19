"""Generic CLI subprocess wrapper with retry logic."""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from multi_model_debate.exceptions import (
    ModelError,
    ModelTimeoutError,
    ModelValidationError,
)
from multi_model_debate.response_parser import is_valid_response

if TYPE_CHECKING:
    from multi_model_debate.config import CLICommandConfig, RetrySettings


@dataclass
class CLIResult:
    """Result of a CLI invocation."""

    stdout: str
    stderr: str
    return_code: int


class CLIModelBackend:
    """Generic wrapper for CLI-based model invocations.

    Implements the ModelBackend protocol by invoking external CLI tools
    via subprocess with retry logic and response validation.
    """

    def __init__(
        self,
        name: str,
        cli_config: CLICommandConfig,
        retry_config: RetrySettings,
        min_response_length: int = 100,
        error_log: Path | None = None,
        default_timeout: int = 300,
    ) -> None:
        """Initialize the CLI model backend.

        Args:
            name: Human-readable model name (e.g., 'GPT', 'Gemini').
            cli_config: CLI command configuration.
            retry_config: Retry settings for exponential backoff.
            min_response_length: Minimum chars for valid response.
            error_log: Optional path to log stderr output.
            default_timeout: Default timeout if not specified in cli_config or call.
        """
        self._name = name
        self.cli_config = cli_config
        self.retry_config = retry_config
        self.min_response_length = min_response_length
        self.error_log = error_log
        # Per-model timeout from config, or global default
        self.default_timeout = cli_config.timeout or default_timeout

    @property
    def name(self) -> str:
        """Human-readable model name."""
        return self._name

    def generate(self, prompt: str, timeout: int | None = None) -> str:
        """Execute CLI with retry logic.

        Args:
            prompt: The input prompt.
            timeout: Maximum time per attempt in seconds. If not specified,
                     uses the model's configured timeout.

        Returns:
            The validated response text.

        Raises:
            ModelError: If all retry attempts fail.
            ModelTimeoutError: If timeout exceeded.
            ModelValidationError: If response fails validation.
        """
        # Use per-model timeout if not explicitly provided
        if timeout is None:
            timeout = self.default_timeout

        last_error: Exception | None = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                result = self._execute(prompt, timeout)
                response = result.stdout
                self._validate_response(response)
                return response

            except subprocess.TimeoutExpired as e:
                last_error = ModelTimeoutError(f"{self.name} timed out after {timeout}s")
                self._log_error(f"Attempt {attempt + 1}: Timeout - {e}")

            except ModelError as e:
                last_error = e
                self._log_error(f"Attempt {attempt + 1}: {e}")

            # Exponential backoff before retry
            if attempt < self.retry_config.max_attempts - 1:
                delay = self.retry_config.base_delay * (2**attempt)
                time.sleep(delay)

        raise ModelError(
            f"{self.name} failed after {self.retry_config.max_attempts} attempts"
        ) from last_error

    def _execute(self, prompt: str, timeout: int) -> CLIResult:
        """Execute the CLI command.

        Args:
            prompt: The input prompt.
            timeout: Maximum time to wait in seconds.

        Returns:
            CLIResult with stdout, stderr, and return code.

        Raises:
            ModelError: If command returns non-zero exit code.
            subprocess.TimeoutExpired: If timeout exceeded.
        """
        cmd = self._build_command(prompt)

        if self.cli_config.input_mode == "stdin":
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        cli_result = CLIResult(
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )

        # Log stderr if present
        if result.stderr:
            self._log_error(f"stderr: {result.stderr}")

        if result.returncode != 0:
            raise ModelError(f"{self.name} returned exit code {result.returncode}: {result.stderr}")

        return cli_result

    def _build_command(self, prompt: str) -> list[str]:
        """Build the command list for subprocess.

        Args:
            prompt: The input prompt (used for positional mode).

        Returns:
            List of command arguments.
        """
        cmd = [self.cli_config.command]

        if self.cli_config.subcommand:
            cmd.append(self.cli_config.subcommand)

        if self.cli_config.flags:
            cmd.extend(self.cli_config.flags)

        if self.cli_config.input_mode == "stdin":
            cmd.append("-")
        else:
            cmd.append(prompt)

        return cmd

    def _validate_response(self, response: str) -> None:
        """Validate the response meets quality criteria.

        Uses JSON-aware validation that accepts:
        - Valid JSON responses (any length)
        - Legacy "NO NEW ISSUES" format (backwards compatibility)
        - Non-JSON responses meeting minimum length

        See REQUIREMENTS_V2.md Section 6 for structured output rationale.

        Args:
            response: The response text to validate.

        Raises:
            ModelValidationError: If validation fails.
        """
        if not response:
            raise ModelValidationError(f"{self.name} returned empty response")

        # Use JSON-aware validation from response_parser
        if is_valid_response(response, self.min_response_length):
            return

        # Provide detailed error with response preview for debugging
        preview = response[:200] + "..." if len(response) > 200 else response
        raise ModelValidationError(
            f"{self.name} response too short ({len(response)} chars, "
            f"min {self.min_response_length}). Preview: {preview!r}"
        )

    def _log_error(self, message: str) -> None:
        """Log an error message to stderr and optionally to file.

        Always logs to stderr for visibility during debugging.
        Also logs to error_log file if configured.

        Args:
            message: The error message to log.
        """
        # Always log to stderr for debugging visibility
        print(f"[{self.name}] {message}", file=sys.stderr)

        # Also log to file if configured
        if self.error_log:
            with open(self.error_log, "a") as f:
                f.write(f"[{self.name}] {message}\n")

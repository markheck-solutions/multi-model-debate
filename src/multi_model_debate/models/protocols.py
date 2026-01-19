"""Protocol definitions for model backends."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ModelBackend(Protocol):
    """Protocol for model backends that can generate responses.

    All models (including Strategist) implement this protocol using
    CLI-based invocation. See REQUIREMENTS_V2.md Section 4.
    """

    @property
    def name(self) -> str:
        """Human-readable model name (e.g., 'GPT', 'Gemini', 'Strategist')."""
        ...

    def generate(self, prompt: str, timeout: int | None = None) -> str:
        """Generate a response from the model.

        Args:
            prompt: The input prompt.
            timeout: Maximum time to wait in seconds. If not specified,
                     uses the model's configured default timeout.

        Returns:
            The model's response text.

        Raises:
            ModelError: If generation fails after retries.
            ModelTimeoutError: If timeout is exceeded.
            ModelValidationError: If response fails validation.
        """
        ...

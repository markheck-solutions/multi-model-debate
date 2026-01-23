"""Exception hierarchy for adversarial critique."""


class AdversarialReviewError(Exception):
    """Base exception for all adversarial review errors."""

    pass


class ConfigError(AdversarialReviewError):
    """Configuration loading or validation error."""

    pass


class ModelError(AdversarialReviewError):
    """Model invocation failed."""

    pass


class ModelTimeoutError(ModelError):
    """Model did not respond within timeout."""

    pass


class ModelValidationError(ModelError):
    """Model response failed validation."""

    pass


class PhaseError(AdversarialReviewError):
    """Phase execution error."""

    pass


class CheckpointError(AdversarialReviewError):
    """Checkpoint loading or saving error."""

    pass


class ReviewError(AdversarialReviewError):
    """General orchestration error."""

    pass


class InsufficientCriticsError(ConfigError):
    """No critics available for adversarial debate.

    Raised when all configured models belong to the same family as
    the Strategist, leaving zero models to serve as critics.
    """

    def __init__(self, strategist: str, available: list[str]) -> None:
        """Initialize with configuration details for actionable error message.

        Args:
            strategist: The strategist model name.
            available: List of available model names from config.
        """
        self.strategist = strategist
        self.available = available
        message = self._build_message()
        super().__init__(message)

    def _build_message(self) -> str:
        """Build actionable error message."""
        available_str = str(self.available)
        return (
            "Only one model family configured.\n\n"
            "Adversarial critique requires at least 2 different model families.\n\n"
            f"Current config: [models].available = {available_str}\n"
            f"Strategist: {self.strategist}\n\n"
            'Fix: Add models from other families (e.g., "codex", "gemini")\n\n'
            "Tip: For single-model review, skip this tool and prompt directly. For example:\n"
            "\"Review this proposal from 3 perspectives: devil's advocate, "
            'domain expert, and end user."'
        )

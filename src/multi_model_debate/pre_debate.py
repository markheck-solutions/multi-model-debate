"""Pre-debate protocol for grounding debates in current context.

This module implements a lightweight pre-debate sequence that injects
the current date into the debate context. This ensures all models are
aware of the current date for relevance assessment.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Mapping

    from multi_model_debate.config import Config
    from multi_model_debate.models.protocols import ModelBackend


console = Console()


@dataclass
class ProtocolResult:
    """Result of the pre-debate protocol."""

    confirmed: bool
    date_context: str


class PreDebateProtocol:
    """Pre-debate protocol for grounding debates in current context.

    Injects the current date into the debate context so models can
    assess proposal relevance against current technology.
    """

    def __init__(
        self,
        models: Mapping[str, ModelBackend],
        config: Config,
    ) -> None:
        """Initialize the pre-debate protocol.

        Args:
            models: Mapping of model name to backend.
            config: Configuration settings.
        """
        self.models = models
        self.config = config
        self.date_context = ""

    def run(self) -> ProtocolResult:
        """Execute the pre-debate protocol.

        Returns:
            ProtocolResult with date context.
        """
        console.print()
        console.print("[bold cyan]PRE-DEBATE PROTOCOL[/bold cyan]")
        console.print()

        # Inject current date context
        self._inject_date()

        console.print("[bold green]Pre-debate protocol complete[/bold green]")
        console.print()

        return ProtocolResult(
            confirmed=True,
            date_context=self.date_context,
        )

    def _inject_date(self) -> None:
        """Set current date context string."""
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        date_long = today.strftime("%B %d, %Y")
        self.date_context = f"Today is {date_str} ({date_long})."
        console.print(f"[dim]Date context: {self.date_context}[/dim]")

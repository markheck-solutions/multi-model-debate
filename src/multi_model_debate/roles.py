"""Dynamic role assignment for adversarial debates.

Assigns Strategist, Critics, and Judge based on who initiated the debate.

DESIGN DECISION: Judge = Strategist's model family (isolated instance)

The Judge evaluates CRITICS, not the Strategist's plan.
Judge reads Critic A vs Critic B arguments and picks winner.
Since Judge is different family from both Critics, no bias.

See REQUIREMENTS_V2.md for full rationale and evidence:
- "Prefer a judge from different provider to reduce shared biases" (Evidently AI, 2026)
- GPT-4 achieves 80% human agreement as judge (LabelYourData, 2026)
- Bias is toward "own writing style" - Judge isn't reading own family's writing
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

from multi_model_debate.exceptions import InsufficientCriticsError

if TYPE_CHECKING:
    from multi_model_debate.config import Config


# Environment variable for explicit strategist override
ENV_STRATEGIST = "ADVERSARIAL_CRITIQUE_STRATEGIST"


@dataclass
class RoleAssignment:
    """Assignment of roles for a debate.

    Attributes:
        strategist: The model family running this session (defends the plan).
        critics: Model families that critique the plan (all except strategist).
        judge: Model family that picks the winner (same as strategist, isolated instance).
    """

    strategist: str
    critics: list[str]
    judge: str


def detect_strategist_family(config: Config) -> str:
    """Detect which model family is running this session.

    Detection priority:
    1. Config override (roles.strategist)
    2. Environment variable (ADVERSARIAL_CRITIQUE_STRATEGIST)
    3. Default to "claude" (most common use case with Claude Code)

    Args:
        config: Configuration with optional strategist override.

    Returns:
        Model family name (e.g., "claude", "gemini", "codex").
    """
    # 1. Check config override
    if config.roles.strategist:
        return config.roles.strategist

    # 2. Check environment variable
    env_strategist = os.environ.get(ENV_STRATEGIST)
    if env_strategist:
        return env_strategist.lower()

    # 3. Default to claude (most common: running from Claude Code)
    return "claude"


def assign_roles(config: Config) -> RoleAssignment:
    """Assign roles for a debate based on config.

    Supports two modes:
    - Explicit: `config.roles.critics` is set - use explicit critic list
    - Legacy: `config.roles.critics` is None - derive from models.available

    Args:
        config: Configuration with available models and role settings.

    Returns:
        RoleAssignment with strategist, critics, and judge.

    Raises:
        ValueError: If strategist is not in available models (legacy mode).
        InsufficientCriticsError: If fewer than 2 critics available.
    """
    strategist = detect_strategist_family(config)

    # Check if explicit mode (critics list provided)
    if config.roles.critics is not None:
        # Explicit mode: use provided critics list
        critics = list(config.roles.critics)  # Copy to avoid mutation

        # Remove strategist from critics if accidentally included
        if strategist in critics:
            warnings.warn(
                f"Strategist '{strategist}' found in critics list, removing automatically",
                UserWarning,
                stacklevel=2,
            )
            critics = [c for c in critics if c != strategist]

        # Validate we still have enough critics
        if len(critics) < 2:
            raise InsufficientCriticsError(strategist=strategist, available=critics)

        # Judge: explicit or default to strategist
        judge = config.roles.judge if config.roles.judge else strategist

    else:
        # Legacy mode: derive critics from available models
        available = config.models.available

        # Validate strategist is available
        if strategist not in available:
            raise ValueError(
                f"Strategist model '{strategist}' not in available models: {available}. "
                f"Add it to [models].available or change the strategist."
            )

        # Critics = all models except strategist's family
        critics = [m for m in available if m != strategist]

        if len(critics) < 1:
            raise InsufficientCriticsError(strategist=strategist, available=available)

        # Judge defaults to strategist (same family, isolated instance)
        judge = strategist

    return RoleAssignment(
        strategist=strategist,
        critics=critics,
        judge=judge,
    )


def get_critic_pair(roles: RoleAssignment) -> tuple[str, str]:
    """Get the first two critics for debate.

    In a 3-model setup (default), this returns the two non-strategist models.
    For example, if strategist is "claude", returns ("codex", "gemini").

    Args:
        roles: The role assignment.

    Returns:
        Tuple of (critic_a, critic_b) model names.

    Raises:
        ValueError: If fewer than 2 critics available.
    """
    if len(roles.critics) < 2:
        raise ValueError(
            f"Need at least 2 critics for debate, got {len(roles.critics)}: {roles.critics}"
        )

    return (roles.critics[0], roles.critics[1])

"""Pytest fixtures for adversarial critique tests."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from multi_model_debate.config import Config


@pytest.fixture
def tmp_run_dir(tmp_path: Path) -> Path:
    """Create a temporary run directory."""
    run_dir = tmp_path / "runs" / "20260101_120000"
    run_dir.mkdir(parents=True)
    return run_dir


@pytest.fixture
def sample_game_plan(tmp_path: Path) -> Path:
    """Create a sample game plan file."""
    game_plan = tmp_path / "game_plan.md"
    game_plan.write_text(
        """# Sample Game Plan

## Goal
Test the adversarial review system.

## Approach
1. Do something
2. Do something else
3. Profit

## Risks
- Things might break
- Users might complain
"""
    )
    return game_plan


@pytest.fixture
def default_config() -> Config:
    """Create a default configuration."""
    from multi_model_debate.config import Config

    return Config.default()


@pytest.fixture
def mock_critic_a() -> MagicMock:
    """Create a mock critic A model backend."""
    model = MagicMock()
    model.name = "codex"
    model.generate.return_value = """ISSUE: Test Issue
SEVERITY: HIGH
CLAIM: Something is wrong
EVIDENCE: "Do something" is vague
FAILURE MODE: Users won't know what to do
"""
    return model


@pytest.fixture
def mock_critic_b() -> MagicMock:
    """Create a mock critic B model backend."""
    model = MagicMock()
    model.name = "gemini"
    model.generate.return_value = """ISSUE: Another Issue
SEVERITY: MEDIUM
CLAIM: Approach is risky
EVIDENCE: "Profit" is not a real step
ASSUMPTION AT RISK: Business model unclear
"""
    return model


@pytest.fixture
def mock_judge() -> MagicMock:
    """Create a mock judge model backend."""
    model = MagicMock()
    model.name = "claude"
    model.generate.return_value = """WINNER: codex

REASONING:
codex raised more concrete issues with specific evidence from the proposal.

KEY ISSUES FROM WINNER:
- Test Issue

CONTESTED POINTS:
- Business model clarity
"""
    return model


@pytest.fixture
def mock_cc1() -> MagicMock:
    """Create a mock CC1 interactive backend."""
    model = MagicMock()
    model.name = "CC1"
    model.request_response.return_value = """ISSUE: Test Issue
RESPONSE: DEFEND
REASONING: The approach is intentionally high-level for flexibility.

DEFENDED: 1
CONCEDED: 0
ESCALATED: 0

POSITION SUMMARY:
The proposal is sound with appropriate flexibility built in.
"""
    return model

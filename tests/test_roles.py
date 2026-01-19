"""Tests for dynamic role assignment."""

import os
from unittest.mock import patch

import pytest

from multi_model_debate.config import Config
from multi_model_debate.exceptions import InsufficientCriticsError
from multi_model_debate.roles import (
    ENV_STRATEGIST,
    RoleAssignment,
    assign_roles,
    detect_strategist_family,
    get_critic_pair,
)


class TestDetectStrategistFamily:
    """Tests for detect_strategist_family function."""

    def test_defaults_to_claude(self) -> None:
        """Test default strategist is claude."""
        config = Config.default()
        result = detect_strategist_family(config)
        assert result == "claude"

    def test_config_override(self) -> None:
        """Test config override takes priority."""
        config = Config.from_dict({"roles": {"strategist": "gemini"}})
        result = detect_strategist_family(config)
        assert result == "gemini"

    def test_env_var_override(self) -> None:
        """Test environment variable override."""
        config = Config.default()
        with patch.dict(os.environ, {ENV_STRATEGIST: "codex"}):
            result = detect_strategist_family(config)
        assert result == "codex"

    def test_config_takes_priority_over_env(self) -> None:
        """Test config override takes priority over env var."""
        config = Config.from_dict({"roles": {"strategist": "gemini"}})
        with patch.dict(os.environ, {ENV_STRATEGIST: "codex"}):
            result = detect_strategist_family(config)
        assert result == "gemini"


class TestAssignRoles:
    """Tests for assign_roles function."""

    def test_claude_as_strategist(self) -> None:
        """Test role assignment when Claude is strategist."""
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini", "codex"]},
            "roles": {"strategist": "claude"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "claude"
        assert roles.judge == "claude"
        assert set(roles.critics) == {"gemini", "codex"}

    def test_gemini_as_strategist(self) -> None:
        """Test role assignment when Gemini is strategist."""
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini", "codex"]},
            "roles": {"strategist": "gemini"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "gemini"
        assert roles.judge == "gemini"
        assert set(roles.critics) == {"claude", "codex"}

    def test_codex_as_strategist(self) -> None:
        """Test role assignment when Codex is strategist."""
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini", "codex"]},
            "roles": {"strategist": "codex"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "codex"
        assert roles.judge == "codex"
        assert set(roles.critics) == {"claude", "gemini"}

    def test_invalid_strategist_raises_error(self) -> None:
        """Test error when strategist not in available models."""
        config = Config.from_dict({
            "models": {"available": ["gemini", "codex"]},
            "roles": {"strategist": "claude"},
        })

        with pytest.raises(ValueError, match="not in available models"):
            assign_roles(config)

    def test_zero_critics_raises_insufficient_critics_error(self) -> None:
        """Test error when only strategist is available (zero critics)."""
        config = Config.from_dict({
            "models": {"available": ["claude"]},
            "roles": {"strategist": "claude"},
        })

        with pytest.raises(InsufficientCriticsError) as exc_info:
            assign_roles(config)

        # Verify error has correct attributes
        assert exc_info.value.strategist == "claude"
        assert exc_info.value.available == ["claude"]

        # Verify error message is actionable
        message = str(exc_info.value)
        assert "Only one model family configured" in message
        assert "at least 2 different model families" in message
        assert "claude" in message
        assert "Fix:" in message
        assert "Tip:" in message

    def test_two_model_setup(self) -> None:
        """Test role assignment with only 2 models."""
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini"]},
            "roles": {"strategist": "claude"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "claude"
        assert roles.judge == "claude"
        assert roles.critics == ["gemini"]

    def test_multiple_families_passes_validation(self) -> None:
        """Test that 2+ different model families passes validation."""
        config = Config.from_dict({
            "models": {"available": ["claude", "codex", "gemini"]},
            "roles": {"strategist": "claude"},
        })

        # Should not raise - we have 2 critics from different families
        roles = assign_roles(config)

        assert roles.strategist == "claude"
        assert len(roles.critics) == 2
        assert set(roles.critics) == {"codex", "gemini"}


class TestGetCriticPair:
    """Tests for get_critic_pair function."""

    def test_returns_first_two_critics(self) -> None:
        """Test that first two critics are returned."""
        roles = RoleAssignment(
            strategist="claude",
            critics=["gemini", "codex"],
            judge="claude",
        )
        critic_a, critic_b = get_critic_pair(roles)

        assert critic_a == "gemini"
        assert critic_b == "codex"

    def test_insufficient_critics_raises_error(self) -> None:
        """Test error when fewer than 2 critics."""
        roles = RoleAssignment(
            strategist="claude",
            critics=["gemini"],
            judge="claude",
        )

        with pytest.raises(ValueError, match="at least 2 critics"):
            get_critic_pair(roles)


class TestRoleAssignmentScenarios:
    """Test various role assignment scenarios from REQUIREMENTS_V2.md."""

    def test_example_claude_strategist(self) -> None:
        """Test example: Claude as Strategist."""
        # From REQUIREMENTS_V2.md table:
        # Strategist=Claude → Critics=Codex+Gemini, Judge=Claude
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini", "codex"]},
            "roles": {"strategist": "claude"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "claude"
        assert set(roles.critics) == {"gemini", "codex"}
        assert roles.judge == "claude"

    def test_example_gemini_strategist(self) -> None:
        """Test example: Gemini as Strategist."""
        # From REQUIREMENTS_V2.md table:
        # Strategist=Gemini → Critics=Claude+Codex, Judge=Gemini
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini", "codex"]},
            "roles": {"strategist": "gemini"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "gemini"
        assert set(roles.critics) == {"claude", "codex"}
        assert roles.judge == "gemini"

    def test_example_codex_strategist(self) -> None:
        """Test example: Codex as Strategist."""
        # From REQUIREMENTS_V2.md table:
        # Strategist=Codex → Critics=Claude+Gemini, Judge=Codex
        config = Config.from_dict({
            "models": {"available": ["claude", "gemini", "codex"]},
            "roles": {"strategist": "codex"},
        })
        roles = assign_roles(config)

        assert roles.strategist == "codex"
        assert set(roles.critics) == {"claude", "gemini"}
        assert roles.judge == "codex"

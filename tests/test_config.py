"""Tests for configuration loading."""

from pathlib import Path

import pytest

from multi_model_debate.config import Config, load_config
from multi_model_debate.exceptions import ConfigError


class TestConfig:
    """Tests for Config class."""

    def test_default_config(self) -> None:
        """Test creating default configuration."""
        config = Config.default()

        assert config.debate.critic_rounds == 4
        assert config.debate.strategist_rounds == 4
        assert config.models.default_timeout == 300
        assert config.models.min_response_length == 100
        assert config.models.available == ["claude", "gemini", "codex"]
        assert config.retry.max_attempts == 3
        assert config.retry.base_delay == 30

    def test_from_dict(self) -> None:
        """Test creating config from dictionary."""
        data = {
            "debate": {"critic_rounds": 2},
            "models": {"default_timeout": 600},
        }
        config = Config.from_dict(data)

        assert config.debate.critic_rounds == 2
        assert config.debate.strategist_rounds == 4  # default
        assert config.models.default_timeout == 600

    def test_from_dict_backwards_compat(self) -> None:
        """Test backwards compatibility with old field names."""
        data = {
            "debate": {"gpt_gemini_rounds": 2, "strategist_winner_rounds": 3},
        }
        config = Config.from_dict(data)

        # Old names should map to new names
        assert config.debate.critic_rounds == 2
        assert config.debate.strategist_rounds == 3

    def test_cli_config_defaults(self) -> None:
        """Test CLI command configuration defaults."""
        config = Config.default()

        assert config.cli.codex.command == "codex"
        assert config.cli.codex.subcommand == "exec"
        assert config.cli.codex.input_mode == "stdin"

        assert config.cli.gemini.command == "gemini"
        assert config.cli.gemini.input_mode == "positional"

        assert config.cli.claude.command == "claude"
        assert config.cli.claude.input_mode == "positional"

    def test_cli_config_dynamic_access(self) -> None:
        """Test CLI config can be accessed by model name."""
        config = Config.default()

        # Access via __getitem__
        assert config.cli["codex"].command == "codex"
        assert config.cli["gemini"].command == "gemini"
        assert config.cli["claude"].command == "claude"

        # Access via get() method
        assert config.cli.get("codex") is not None
        assert config.cli.get("nonexistent") is None

    def test_cli_config_raises_on_missing(self) -> None:
        """Test that accessing non-existent model raises KeyError."""
        config = Config.default()

        with pytest.raises(KeyError, match="No CLI configuration for model"):
            _ = config.cli["nonexistent_model"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_nonexistent_returns_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing config file returns defaults."""
        # Change to a temp directory with no config file
        monkeypatch.chdir(tmp_path)
        config = load_config(None)
        assert config == Config.default()

    def test_load_from_toml(self, tmp_path: Path) -> None:
        """Test loading config from TOML file."""
        config_file = tmp_path / "multi_model_debate.toml"
        config_file.write_text(
            """
[debate]
critic_rounds = 3

[models]
available = ["claude", "codex"]
default_timeout = 120
"""
        )

        config = load_config(config_file)

        assert config.debate.critic_rounds == 3
        assert config.models.default_timeout == 120
        assert config.models.available == ["claude", "codex"]

    def test_load_invalid_toml_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid TOML raises ConfigError."""
        config_file = tmp_path / "bad.toml"
        config_file.write_text("this is not valid toml [[[")

        with pytest.raises(ConfigError):
            Config.from_toml(config_file)

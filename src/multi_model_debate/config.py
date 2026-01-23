"""Configuration management with Pydantic and TOML."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from multi_model_debate.exceptions import ConfigError


class DebateSettings(BaseModel):
    """Settings for debate rounds."""

    critic_rounds: int = Field(default=4, ge=1, le=10)
    strategist_rounds: int = Field(default=4, ge=1, le=10)
    # Backwards compatibility aliases
    gpt_gemini_rounds: int | None = Field(default=None, exclude=True)
    strategist_winner_rounds: int | None = Field(default=None, exclude=True)

    def model_post_init(self, __context: Any) -> None:
        """Handle backwards compatibility for renamed fields."""
        if self.gpt_gemini_rounds is not None:
            object.__setattr__(self, "critic_rounds", self.gpt_gemini_rounds)
        if self.strategist_winner_rounds is not None:
            object.__setattr__(self, "strategist_rounds", self.strategist_winner_rounds)


class RetrySettings(BaseModel):
    """Settings for retry logic with exponential backoff."""

    max_attempts: int = Field(default=3, ge=1)
    base_delay: int = Field(default=30, ge=1, description="Base delay in seconds")


class ModelSettings(BaseModel):
    """Settings for model invocations."""

    available: list[str] = Field(
        default_factory=lambda: ["claude", "gemini", "codex"],
        description="Available model families for debates",
    )
    default_timeout: int = Field(default=300, ge=30, description="Timeout in seconds")
    min_response_length: int = Field(default=100, ge=10)


class CLICommandConfig(BaseModel):
    """Configuration for a CLI command."""

    command: str
    subcommand: str | None = None
    flags: list[str] = Field(default_factory=list)
    input_mode: str = Field(default="positional", pattern="^(positional|stdin)$")
    timeout: int | None = Field(
        default=None,
        ge=30,
        description="Per-model timeout in seconds. If not set, uses models.default_timeout.",
    )


class CLISettings(BaseModel):
    """CLI command configurations for each model.

    Supports dynamic model names via __getitem__ access.
    Default configurations provided for claude, gemini, codex.
    """

    model_config = {"extra": "allow"}  # Allow dynamic model names

    codex: CLICommandConfig = Field(
        default_factory=lambda: CLICommandConfig(
            command="codex",
            subcommand="exec",
            input_mode="stdin",
        )
    )
    gemini: CLICommandConfig = Field(
        default_factory=lambda: CLICommandConfig(
            command="gemini",
            input_mode="positional",
        )
    )
    claude: CLICommandConfig = Field(
        default_factory=lambda: CLICommandConfig(
            command="claude",
            input_mode="positional",
            flags=[
                "-p",
                "--tools",
                "",
                "--",
            ],  # Print mode, disable built-in tools, -- terminates options
        )
    )

    def __getitem__(self, name: str) -> CLICommandConfig:
        """Get CLI config for a model by name."""
        if hasattr(self, name):
            value = getattr(self, name)
            if isinstance(value, CLICommandConfig):
                return value
        # Check for extra fields (dynamic models)
        extra = self.model_extra or {}
        if name in extra:
            return CLICommandConfig.model_validate(extra[name])
        raise KeyError(f"No CLI configuration for model: {name}")

    def get(self, name: str, default: CLICommandConfig | None = None) -> CLICommandConfig | None:
        """Get CLI config for a model, with optional default."""
        try:
            return self[name]
        except KeyError:
            return default


class NotificationSettings(BaseModel):
    """Settings for desktop notifications."""

    enabled: bool = True
    command: str = "notify-send"


class RolesSettings(BaseModel):
    """Settings for dynamic role assignment.

    Supports two modes:
    - Legacy: Only `strategist` set, derive critics from models.available
    - Explicit: `critics` list set, use explicit assignments

    DESIGN DECISION: Judge defaults to Strategist's model family (isolated instance)

    The Judge evaluates CRITICS, not the Strategist's plan.
    Judge reads Critic A vs Critic B arguments and picks winner.
    Since Judge is different family from both Critics, no bias.
    """

    strategist: str | None = Field(
        default=None,
        description="Override strategist model family. If not set, auto-detect from environment.",
    )
    critics: list[str] | None = Field(
        default=None,
        description="Explicit list of critic model families. If not set, derived from available.",
    )
    judge: str | None = Field(
        default=None,
        description="Judge model family. If not set, defaults to strategist.",
    )

    @model_validator(mode="after")
    def validate_explicit_critics(self) -> RolesSettings:
        """Validate explicit critic configuration."""
        if self.critics is not None:
            if len(self.critics) < 2:
                raise ValueError("At least 2 critics required for adversarial debate")
            if len(self.critics) != len(set(self.critics)):
                raise ValueError("Duplicate critics not allowed")
        return self


class PreDebateSettings(BaseModel):
    """Settings for the pre-debate protocol.

    The pre-debate protocol injects the current date context so models
    can assess proposal relevance against current technology.
    """

    enabled: bool = Field(
        default=True,
        description="Enable the pre-debate protocol.",
    )


class Config(BaseModel):
    """Main configuration container."""

    debate: DebateSettings = Field(default_factory=DebateSettings)
    retry: RetrySettings = Field(default_factory=RetrySettings)
    models: ModelSettings = Field(default_factory=ModelSettings)
    cli: CLISettings = Field(default_factory=CLISettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    roles: RolesSettings = Field(default_factory=RolesSettings)
    pre_debate: PreDebateSettings = Field(default_factory=PreDebateSettings)

    @classmethod
    def from_toml(cls, path: Path) -> Config:
        """Load configuration from a TOML file."""
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            return cls.model_validate(data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Invalid TOML in {path}: {e}") from e
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}") from e

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create configuration from a dictionary."""
        return cls.model_validate(data)

    @classmethod
    def default(cls) -> Config:
        """Create default configuration."""
        return cls()


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """Search for config file in current directory and parents.

    Looks for:
    - multi_model_debate.toml
    - .multi_model_debate.toml
    - pyproject.toml (with [tool.multi-model-debate] section)
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while current != current.parent:
        # Check for dedicated config files
        for name in ["multi_model_debate.toml", ".multi_model_debate.toml"]:
            config_path = current / name
            if config_path.exists():
                return config_path

        # Check pyproject.toml for tool section
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                if "tool" in data and "multi-model-debate" in data["tool"]:
                    return pyproject
            except tomllib.TOMLDecodeError:
                pass

        current = current.parent

    return None


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file or use defaults.

    Args:
        config_path: Explicit path to config file. If None, searches for config.

    Returns:
        Loaded or default configuration.
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None:
        return Config.default()

    # Handle pyproject.toml specially
    if config_path.name == "pyproject.toml":
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        tool_config = data.get("tool", {}).get("multi-model-debate", {})
        return Config.from_dict(tool_config)

    return Config.from_toml(config_path)

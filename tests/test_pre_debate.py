"""Tests for the pre-debate protocol."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from multi_model_debate.config import Config
from multi_model_debate.pre_debate import PreDebateProtocol, ProtocolResult


@pytest.fixture
def mock_models() -> dict[str, MagicMock]:
    """Create mock model backends."""
    models = {}
    for name in ["claude", "gemini", "codex"]:
        mock = MagicMock()
        mock.name = name
        models[name] = mock
    return models


@pytest.fixture
def config() -> Config:
    """Create test configuration."""
    return Config.from_dict(
        {
            "models": {"available": ["claude", "gemini", "codex"]},
            "pre_debate": {"enabled": True},
        }
    )


class TestPreDebateProtocol:
    """Tests for PreDebateProtocol class."""

    def test_init(self, mock_models: dict, config: Config) -> None:
        """Test protocol initialization."""
        protocol = PreDebateProtocol(models=mock_models, config=config)
        assert protocol.models == mock_models
        assert protocol.config == config
        assert protocol.date_context == ""

    def test_inject_date(self, mock_models: dict, config: Config) -> None:
        """Test date injection sets context string."""
        protocol = PreDebateProtocol(models=mock_models, config=config)
        protocol._inject_date()

        today = datetime.now()
        assert today.strftime("%Y-%m-%d") in protocol.date_context
        assert "Today is" in protocol.date_context

    def test_run_returns_result(self, mock_models: dict, config: Config) -> None:
        """Test run returns ProtocolResult with date context."""
        protocol = PreDebateProtocol(models=mock_models, config=config)
        result = protocol.run()

        assert isinstance(result, ProtocolResult)
        assert result.confirmed is True
        assert result.date_context != ""
        assert "Today is" in result.date_context

    def test_run_includes_date(self, mock_models: dict, config: Config) -> None:
        """Test run includes current date in context."""
        protocol = PreDebateProtocol(models=mock_models, config=config)
        result = protocol.run()

        today = datetime.now()
        assert today.strftime("%Y-%m-%d") in result.date_context


class TestProtocolResult:
    """Tests for ProtocolResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a protocol result."""
        result = ProtocolResult(
            confirmed=True,
            date_context="Today is 2026-01-08.",
        )
        assert result.confirmed is True
        assert result.date_context == "Today is 2026-01-08."

    def test_result_fields(self) -> None:
        """Test ProtocolResult has expected fields."""
        result = ProtocolResult(
            confirmed=False,
            date_context="",
        )
        assert hasattr(result, "confirmed")
        assert hasattr(result, "date_context")

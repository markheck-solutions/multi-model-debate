"""Tests for Phase base classes and artifact handling."""

import json
from pathlib import Path

import pytest

from multi_model_debate.phases.base import PhaseArtifact


class TestPhaseArtifactJsonSaving:
    """Tests for JSON artifact saving with fence stripping."""

    def test_write_strips_json_fences(self, tmp_path: Path) -> None:
        """Test that JSON fences are stripped when is_json=True."""
        artifact = PhaseArtifact(
            name="test",
            path=tmp_path / "test.json",
            is_json=True,
        )

        # Write content with markdown fences
        content = '```json\n{"has_new_issues": true, "issues": []}\n```'
        artifact.write(content)

        # Read back and verify fences were stripped
        saved = artifact.path.read_text()
        assert not saved.startswith("```")
        assert not saved.endswith("```")

        # Verify it's valid JSON
        data = json.loads(saved)
        assert data["has_new_issues"] is True

    def test_write_preserves_clean_json(self, tmp_path: Path) -> None:
        """Test that already-clean JSON is preserved."""
        artifact = PhaseArtifact(
            name="test",
            path=tmp_path / "test.json",
            is_json=True,
        )

        # Write clean JSON (no fences)
        content = '{"has_new_issues": false}'
        artifact.write(content)

        saved = artifact.path.read_text()
        assert saved == content

    def test_write_non_json_preserves_content(self, tmp_path: Path) -> None:
        """Test that non-JSON artifacts preserve content as-is."""
        artifact = PhaseArtifact(
            name="test",
            path=tmp_path / "test.md",
            is_json=False,
        )

        content = "# Markdown Content\n\nSome text here."
        artifact.write(content)

        saved = artifact.path.read_text()
        assert saved == content


class TestPhaseArtifactOperations:
    """Tests for artifact exists, is_valid, and read operations."""

    def test_exists_returns_true_when_file_exists(self, tmp_path: Path) -> None:
        """Test that exists() returns True when file exists."""
        path = tmp_path / "test.json"
        path.write_text("content")

        artifact = PhaseArtifact(
            name="test",
            path=path,
            is_json=True,
        )

        assert artifact.exists()

    def test_exists_returns_false_when_file_missing(self, tmp_path: Path) -> None:
        """Test that exists() returns False when file missing."""
        artifact = PhaseArtifact(
            name="test",
            path=tmp_path / "nonexistent.json",
            is_json=True,
        )

        assert not artifact.exists()

    def test_is_valid_with_valid_content(self, tmp_path: Path) -> None:
        """Test that is_valid() returns True for valid content."""
        path = tmp_path / "test.json"
        path.write_text("x" * 150)

        artifact = PhaseArtifact(
            name="test",
            path=path,
            is_json=True,
            min_length=100,
        )

        assert artifact.is_valid()

    def test_is_valid_with_short_content(self, tmp_path: Path) -> None:
        """Test that is_valid() returns False for too-short content."""
        path = tmp_path / "test.json"
        path.write_text("short")

        artifact = PhaseArtifact(
            name="test",
            path=path,
            is_json=True,
            min_length=100,
        )

        assert not artifact.is_valid()

    def test_is_valid_when_file_missing(self, tmp_path: Path) -> None:
        """Test that is_valid() returns False when file missing."""
        artifact = PhaseArtifact(
            name="test",
            path=tmp_path / "nonexistent.json",
            is_json=True,
            min_length=100,
        )

        assert not artifact.is_valid()

    def test_read_returns_content(self, tmp_path: Path) -> None:
        """Test that read() returns file content."""
        path = tmp_path / "test.json"
        path.write_text("test content")

        artifact = PhaseArtifact(
            name="test",
            path=path,
            is_json=True,
        )

        assert artifact.read() == "test content"

    def test_read_raises_when_file_missing(self, tmp_path: Path) -> None:
        """Test that read() raises FileNotFoundError when file missing."""
        artifact = PhaseArtifact(
            name="test",
            path=tmp_path / "nonexistent.json",
            is_json=True,
        )

        with pytest.raises(FileNotFoundError):
            artifact.read()


class TestPhaseArtifactJsonExtension:
    """Tests for JSON artifact file extension."""

    def test_json_artifact_uses_json_extension(self, tmp_path: Path) -> None:
        """Test that JSON artifacts use .json extension."""
        artifact = PhaseArtifact(
            name="p1_codex_baseline",
            path=tmp_path / "p1_codex_baseline.json",
            is_json=True,
        )

        artifact.write('```json\n{"test": true}\n```')

        assert artifact.path.suffix == ".json"
        assert artifact.path.exists()

    def test_md_artifact_uses_md_extension(self, tmp_path: Path) -> None:
        """Test that non-JSON artifacts use .md extension."""
        artifact = PhaseArtifact(
            name="p4_peer_review",
            path=tmp_path / "p4_peer_review.md",
            is_json=False,
        )

        artifact.write("# Peer Review\n\nContent here.")

        assert artifact.path.suffix == ".md"
        assert artifact.path.exists()

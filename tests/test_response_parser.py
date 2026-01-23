"""Tests for the response parser module."""

import pytest

from multi_model_debate.response_parser import (
    CURRENT_SCHEMA_VERSION,
    LEGACY_SCHEMA_VERSION,
    Issue,
    ParsedResponse,
    ResponseParseError,
    extract_json_block,
    has_new_issues,
    is_legacy_no_issues,
    is_valid_response,
    parse_json_response,
    parse_response,
)


class TestExtractJsonBlock:
    """Tests for extract_json_block function."""

    def test_extracts_json_from_code_block(self) -> None:
        """Test extracting JSON from a code block."""
        response = """Here is my analysis:

```json
{
  "has_new_issues": true,
  "issues": []
}
```

That's my response."""
        result = extract_json_block(response)
        assert result is not None
        assert '"has_new_issues": true' in result

    def test_returns_none_when_no_block(self) -> None:
        """Test returns None when no JSON block present."""
        response = "This is just plain text without any JSON."
        result = extract_json_block(response)
        assert result is None

    def test_handles_multiline_json(self) -> None:
        """Test handling of multiline JSON blocks."""
        response = """```json
{
  "has_new_issues": true,
  "issues": [
    {
      "id": "ISSUE-001",
      "title": "Test"
    }
  ]
}
```"""
        result = extract_json_block(response)
        assert result is not None
        assert "ISSUE-001" in result


class TestParseJsonResponse:
    """Tests for parse_json_response function."""

    def test_parses_json_block(self) -> None:
        """Test parsing JSON from code block."""
        response = """```json
{"has_new_issues": true, "issues": [], "summary": "test"}
```"""
        result = parse_json_response(response)
        assert result["has_new_issues"] is True
        assert result["summary"] == "test"

    def test_parses_raw_json(self) -> None:
        """Test parsing raw JSON without code block."""
        response = '{"has_new_issues": false, "issues": []}'
        result = parse_json_response(response)
        assert result["has_new_issues"] is False

    def test_finds_json_in_text(self) -> None:
        """Test finding JSON object embedded in text."""
        response = """Some preamble text
{"has_new_issues": true, "issues": []}
Some trailing text"""
        result = parse_json_response(response)
        assert result["has_new_issues"] is True

    def test_raises_on_invalid_json(self) -> None:
        """Test raises error when JSON cannot be parsed."""
        response = "This is not JSON at all"
        with pytest.raises(ResponseParseError):
            parse_json_response(response)


class TestParseResponse:
    """Tests for parse_response function."""

    def test_parses_json_response(self) -> None:
        """Test parsing a proper JSON response."""
        response = """```json
{
  "has_new_issues": true,
  "issues": [
    {
      "id": "ISSUE-001",
      "severity": "HIGH",
      "title": "Test Issue",
      "claim": "Something is wrong"
    }
  ],
  "summary": "Found one issue"
}
```"""
        result = parse_response(response)
        assert isinstance(result, ParsedResponse)
        assert result.has_new_issues is True
        assert len(result.issues) == 1
        assert result.issues[0].id == "ISSUE-001"
        assert result.issues[0].severity == "HIGH"

    def test_handles_legacy_no_issues(self) -> None:
        """Test handling legacy NO NEW ISSUES format."""
        response = "NO NEW ISSUES. Previous critiques cover all concerns."
        result = parse_response(response)
        assert result.has_new_issues is False
        assert len(result.issues) == 0

    def test_handles_legacy_no_issues_case_insensitive(self) -> None:
        """Test legacy format is case insensitive."""
        response = "no new issues. Everything is covered."
        result = parse_response(response)
        assert result.has_new_issues is False

    def test_fallback_assumes_issues_on_unparseable(self) -> None:
        """Test fallback assumes issues exist for unparseable responses."""
        response = "This is a long response that cannot be parsed as JSON " * 10
        result = parse_response(response)
        assert result.has_new_issues is True
        assert len(result.issues) == 0
        assert result.raw_response == response


class TestIssue:
    """Tests for Issue dataclass."""

    def test_from_dict_full(self) -> None:
        """Test creating Issue from complete dictionary."""
        data = {
            "id": "ISSUE-001",
            "severity": "HIGH",
            "title": "Test Issue",
            "claim": "Something is wrong",
            "evidence": "See line 42",
            "recommendation": "Fix it",
            "failure_mode": "System crashes",
        }
        issue = Issue.from_dict(data)
        assert issue.id == "ISSUE-001"
        assert issue.severity == "HIGH"
        assert issue.failure_mode == "System crashes"

    def test_from_dict_partial(self) -> None:
        """Test creating Issue from partial dictionary."""
        data = {"id": "ISSUE-001", "severity": "LOW", "title": "Minor"}
        issue = Issue.from_dict(data)
        assert issue.id == "ISSUE-001"
        assert issue.claim == ""
        assert issue.evidence == ""


class TestHasNewIssues:
    """Tests for has_new_issues function."""

    def test_returns_true_for_json_with_issues(self) -> None:
        """Test returns True when JSON indicates issues."""
        response = '{"has_new_issues": true, "issues": []}'
        assert has_new_issues(response) is True

    def test_returns_false_for_json_without_issues(self) -> None:
        """Test returns False when JSON indicates no issues."""
        response = '{"has_new_issues": false, "issues": []}'
        assert has_new_issues(response) is False

    def test_returns_false_for_legacy_no_issues(self) -> None:
        """Test returns False for legacy NO NEW ISSUES format."""
        response = "NO NEW ISSUES"
        assert has_new_issues(response) is False


class TestIsLegacyNoIssues:
    """Tests for is_legacy_no_issues function."""

    def test_detects_uppercase(self) -> None:
        """Test detects uppercase NO NEW ISSUES."""
        assert is_legacy_no_issues("NO NEW ISSUES") is True

    def test_detects_lowercase(self) -> None:
        """Test detects lowercase no new issues."""
        assert is_legacy_no_issues("no new issues") is True

    def test_detects_in_sentence(self) -> None:
        """Test detects phrase in a sentence."""
        response = "After review, I have NO NEW ISSUES to raise."
        assert is_legacy_no_issues(response) is True

    def test_returns_false_for_other_text(self) -> None:
        """Test returns False for unrelated text."""
        assert is_legacy_no_issues("Here are some issues") is False


class TestIsValidResponse:
    """Tests for is_valid_response function."""

    def test_empty_response_invalid(self) -> None:
        """Test empty response is invalid."""
        assert is_valid_response("") is False
        assert is_valid_response("   ") is False

    def test_json_response_valid_any_length(self) -> None:
        """Test JSON response is valid regardless of length."""
        response = '```json\n{"has_new_issues": false}\n```'
        assert is_valid_response(response, min_length=1000) is True

    def test_legacy_no_issues_valid(self) -> None:
        """Test legacy NO NEW ISSUES is valid."""
        assert is_valid_response("NO NEW ISSUES", min_length=1000) is True

    def test_short_response_invalid(self) -> None:
        """Test short non-JSON response is invalid."""
        assert is_valid_response("Short", min_length=100) is False

    def test_long_response_valid(self) -> None:
        """Test long enough response is valid."""
        response = "A" * 100
        assert is_valid_response(response, min_length=100) is True


class TestParsedResponse:
    """Tests for ParsedResponse dataclass."""

    def test_issue_count(self) -> None:
        """Test issue_count method."""
        response = ParsedResponse(
            has_new_issues=True,
            issues=[
                Issue("ID-1", "HIGH", "Title 1"),
                Issue("ID-2", "LOW", "Title 2"),
            ],
        )
        assert response.issue_count() == 2

    def test_issue_count_empty(self) -> None:
        """Test issue_count with no issues."""
        response = ParsedResponse(has_new_issues=False, issues=[])
        assert response.issue_count() == 0


class TestSchemaVersioning:
    """Tests for schema versioning in responses."""

    def test_parse_response_with_version(self) -> None:
        """Test parsing response with schema_version field."""
        response = """```json
{
  "schema_version": "1.0",
  "has_new_issues": true,
  "issues": [],
  "summary": "Test"
}
```"""
        result = parse_response(response)
        assert result.schema_version == "1.0"

    def test_parse_response_without_version_defaults_to_legacy(self) -> None:
        """Test parsing response without version defaults to legacy."""
        response = """```json
{
  "has_new_issues": true,
  "issues": [],
  "summary": "Test"
}
```"""
        result = parse_response(response)
        assert result.schema_version == LEGACY_SCHEMA_VERSION

    def test_legacy_no_issues_gets_legacy_version(self) -> None:
        """Test legacy NO NEW ISSUES format gets legacy version."""
        response = "NO NEW ISSUES"
        result = parse_response(response)
        assert result.schema_version == LEGACY_SCHEMA_VERSION

    def test_unparseable_response_gets_legacy_version(self) -> None:
        """Test unparseable response defaults to legacy version."""
        response = "This is not JSON at all " * 10
        result = parse_response(response)
        assert result.schema_version == LEGACY_SCHEMA_VERSION

    def test_schema_version_preserved_in_parsed_response(self) -> None:
        """Test schema version is preserved in ParsedResponse."""
        response = """```json
{
  "schema_version": "2.0",
  "has_new_issues": false,
  "issues": [],
  "summary": "Future version"
}
```"""
        result = parse_response(response)
        assert result.schema_version == "2.0"

    def test_current_schema_version_constant(self) -> None:
        """Test CURRENT_SCHEMA_VERSION is set correctly."""
        assert CURRENT_SCHEMA_VERSION == "1.0"

    def test_legacy_schema_version_constant(self) -> None:
        """Test LEGACY_SCHEMA_VERSION is set correctly."""
        assert LEGACY_SCHEMA_VERSION == "0.9"

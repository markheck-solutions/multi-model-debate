"""Structured response parser for model outputs.

This module provides JSON parsing for model responses, replacing the
legacy magic string detection ("NO NEW ISSUES") with structured output.

See REQUIREMENTS_V2.md Section 6 for rationale.

Schema Versioning:
- Version 1.0: Current format with schema_version field
- Version 0.9: Legacy format without schema_version (backwards compat)
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

# Current expected schema version
CURRENT_SCHEMA_VERSION = "1.0"
# Default version for responses without schema_version (backwards compat)
LEGACY_SCHEMA_VERSION = "0.9"

logger = logging.getLogger(__name__)


class ResponseParseError(Exception):
    """Error parsing model response."""

    pass


@dataclass
class Issue:
    """A structured issue from a model response."""

    id: str
    severity: str
    title: str
    claim: str = ""
    evidence: str = ""
    recommendation: str = ""
    failure_mode: str = ""  # GPT lens uses this
    assumption_at_risk: str = ""  # Gemini lens uses this

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Issue:
        """Create an Issue from a dictionary."""
        return cls(
            id=data.get("id", "UNKNOWN"),
            severity=data.get("severity", "MEDIUM"),
            title=data.get("title", "Untitled Issue"),
            claim=data.get("claim", ""),
            evidence=data.get("evidence", ""),
            recommendation=data.get("recommendation", ""),
            failure_mode=data.get("failure_mode", ""),
            assumption_at_risk=data.get("assumption_at_risk", ""),
        )


@dataclass
class ParsedResponse:
    """A parsed model response with structured data."""

    has_new_issues: bool
    issues: list[Issue] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    schema_version: str = LEGACY_SCHEMA_VERSION

    def issue_count(self) -> int:
        """Return the number of issues."""
        return len(self.issues)


def extract_json_block(response: str) -> str | None:
    """Extract JSON from a ```json code block.

    Args:
        response: The raw response text.

    Returns:
        The JSON string if found, None otherwise.
    """
    # Try to find ```json block
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def parse_json_response(response: str) -> dict[str, Any]:
    """Parse JSON from a model response.

    Tries multiple strategies:
    1. Extract from ```json code block
    2. Parse entire response as JSON
    3. Find JSON object anywhere in response

    Args:
        response: The raw response text.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        ResponseParseError: If JSON cannot be parsed.
    """
    # Strategy 1: Extract from ```json block
    json_block = extract_json_block(response)
    if json_block:
        try:
            result: dict[str, Any] = json.loads(json_block)
            return result
        except json.JSONDecodeError:
            # Continue to other strategies
            pass

    # Strategy 2: Try parsing entire response as JSON
    try:
        result = json.loads(response.strip())
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find JSON object anywhere in response
    # Look for {...} pattern
    json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.findall(json_pattern, response, re.DOTALL)
    for match in matches:
        try:
            data = json.loads(match)
            # Verify it has expected structure
            if isinstance(data, dict) and "has_new_issues" in data:
                return data
        except json.JSONDecodeError:
            continue

    raise ResponseParseError(
        f"Could not parse JSON from response. Response starts with: {response[:200]}..."
    )


def parse_response(response: str) -> ParsedResponse:
    """Parse a model response into structured data.

    Handles both new JSON format and legacy "NO NEW ISSUES" format
    for backwards compatibility.

    Args:
        response: The raw response text.

    Returns:
        ParsedResponse with structured data.
    """
    # Check for legacy "NO NEW ISSUES" format (backwards compatibility)
    if is_legacy_no_issues(response):
        return ParsedResponse(
            has_new_issues=False,
            issues=[],
            summary="No new issues identified.",
            raw_response=response,
            schema_version=LEGACY_SCHEMA_VERSION,
        )

    # Try to parse as JSON
    try:
        data = parse_json_response(response)

        # Extract schema version with backwards compatibility
        schema_version = data.get("schema_version", LEGACY_SCHEMA_VERSION)
        if schema_version == LEGACY_SCHEMA_VERSION:
            logger.warning(
                "Response missing schema_version field; assuming version %s. "
                "Update prompts to include schema_version for better compatibility.",
                LEGACY_SCHEMA_VERSION,
            )
        elif schema_version != CURRENT_SCHEMA_VERSION:
            logger.warning(
                "Response has unexpected schema_version '%s' (expected '%s'). "
                "Parsing may produce unexpected results.",
                schema_version,
                CURRENT_SCHEMA_VERSION,
            )

        return ParsedResponse(
            has_new_issues=data.get("has_new_issues", True),
            issues=[Issue.from_dict(i) for i in data.get("issues", [])],
            summary=data.get("summary", ""),
            raw_response=response,
            schema_version=schema_version,
        )
    except ResponseParseError:
        # Fallback: assume there are issues if we can't parse
        # This maintains the prior behavior where any substantial response
        # was treated as containing issues
        return ParsedResponse(
            has_new_issues=True,
            issues=[],
            summary="",
            raw_response=response,
            schema_version=LEGACY_SCHEMA_VERSION,
        )


def is_legacy_no_issues(response: str) -> bool:
    """Check if response uses legacy "NO NEW ISSUES" format.

    This provides backwards compatibility with older prompts and
    responses that haven't been updated to JSON format.

    Args:
        response: The raw response text.

    Returns:
        True if this is a legacy no-issues response.
    """
    return "NO NEW ISSUES" in response.upper()


def has_new_issues(response: str) -> bool:
    """Check if a response indicates new issues were found.

    This is the main entry point for checking if debate should continue.
    Works with both JSON format and legacy "NO NEW ISSUES" format.

    Args:
        response: The raw response text (or parsed JSON string).

    Returns:
        True if the response contains new issues.
    """
    parsed = parse_response(response)
    return parsed.has_new_issues


def is_valid_response(response: str, min_length: int = 100) -> bool:
    """Check if a response is valid for processing.

    A response is valid if:
    - It's a proper JSON response (regardless of length)
    - It uses legacy "NO NEW ISSUES" format
    - It meets minimum length requirements

    Args:
        response: The raw response text.
        min_length: Minimum length for non-JSON responses.

    Returns:
        True if the response is valid.
    """
    if not response or not response.strip():
        return False

    # Check for JSON format
    if extract_json_block(response) is not None:
        return True

    # Check for legacy format
    if is_legacy_no_issues(response):
        return True

    # Fall back to length check
    return len(response) >= min_length

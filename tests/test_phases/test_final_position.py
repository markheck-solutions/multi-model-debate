"""Tests for Phase 6: Final Position, including checklist validation."""

from multi_model_debate.phases.final_position import (
    VALID_CHECKLIST_STATUSES,
    ChecklistCoverage,
    ChecklistItem,
    calculate_coverage,
    parse_checklist,
)


class TestChecklistItem:
    """Tests for ChecklistItem dataclass."""

    def test_valid_status_addressed(self) -> None:
        """Test ADDRESSED is a valid status."""
        item = ChecklistItem("ISSUE-001", "Title", "Response", "ADDRESSED")
        assert item.is_valid_status is True

    def test_valid_status_rejected(self) -> None:
        """Test REJECTED is a valid status."""
        item = ChecklistItem("ISSUE-001", "Title", "Response", "REJECTED")
        assert item.is_valid_status is True

    def test_valid_status_deferred(self) -> None:
        """Test DEFERRED is a valid status."""
        item = ChecklistItem("ISSUE-001", "Title", "Response", "DEFERRED")
        assert item.is_valid_status is True

    def test_valid_status_not_applicable(self) -> None:
        """Test NOT_APPLICABLE is a valid status."""
        item = ChecklistItem("ISSUE-001", "Title", "Response", "NOT_APPLICABLE")
        assert item.is_valid_status is True

    def test_valid_status_case_insensitive(self) -> None:
        """Test status validation is case insensitive."""
        item = ChecklistItem("ISSUE-001", "Title", "Response", "addressed")
        assert item.is_valid_status is True

    def test_invalid_status(self) -> None:
        """Test invalid status returns False."""
        item = ChecklistItem("ISSUE-001", "Title", "Response", "UNKNOWN")
        assert item.is_valid_status is False


class TestParseChecklist:
    """Tests for parse_checklist function."""

    def test_parse_valid_checklist(self) -> None:
        """Test parsing a valid checklist section."""
        content = """
## 9. ISSUE RESPONSE CHECKLIST

| Issue ID | Title | Response | Status |
|----------|-------|----------|--------|
| ISSUE-001 | Role assignment bias | Defended: Judge evaluates critics | ADDRESSED |
| ISSUE-002 | Env-var detection | Conceded: Will document | ADDRESSED |
| ISSUE-003 | Research step undefined | N/A: Removed in v4 | NOT_APPLICABLE |

## WHAT WOULD YOU LIKE TO DO?
"""
        items = parse_checklist(content)
        assert len(items) == 3
        assert items[0].issue_id == "ISSUE-001"
        assert items[0].status == "ADDRESSED"
        assert items[2].status == "NOT_APPLICABLE"

    def test_parse_checklist_missing_section(self) -> None:
        """Test returns empty list when checklist section is missing."""
        content = """
## 8. MY RECOMMENDATION

Here is my recommendation.

## WHAT WOULD YOU LIKE TO DO?
"""
        items = parse_checklist(content)
        assert items == []

    def test_parse_checklist_empty_table(self) -> None:
        """Test returns empty list when table has only headers."""
        content = """
## 9. ISSUE RESPONSE CHECKLIST

| Issue ID | Title | Response | Status |
|----------|-------|----------|--------|

## WHAT WOULD YOU LIKE TO DO?
"""
        items = parse_checklist(content)
        assert items == []

    def test_parse_checklist_without_section_number(self) -> None:
        """Test parsing checklist without the '9.' prefix."""
        content = """
## ISSUE RESPONSE CHECKLIST

| Issue ID | Title | Response | Status |
|----------|-------|----------|--------|
| ISSUE-001 | Test | Test response | ADDRESSED |
"""
        items = parse_checklist(content)
        assert len(items) == 1

    def test_parse_checklist_skips_header_row(self) -> None:
        """Test that header row is not included in results."""
        content = """
## 9. ISSUE RESPONSE CHECKLIST

| Issue ID | Title | Response | Status |
|----------|-------|----------|--------|
| ISSUE-001 | Test | Response | ADDRESSED |
"""
        items = parse_checklist(content)
        assert len(items) == 1
        assert items[0].issue_id == "ISSUE-001"

    def test_parse_checklist_preserves_response_text(self) -> None:
        """Test that response text is preserved correctly."""
        content = """
## 9. ISSUE RESPONSE CHECKLIST

| Issue ID | Title | Response | Status |
|----------|-------|----------|--------|
| ISSUE-001 | Test | Defended: This is my detailed response | ADDRESSED |
"""
        items = parse_checklist(content)
        assert items[0].response == "Defended: This is my detailed response"


class TestCalculateCoverage:
    """Tests for calculate_coverage function."""

    def test_coverage_all_addressed(self) -> None:
        """Test coverage with all items addressed."""
        items = [
            ChecklistItem("ISSUE-001", "T1", "R1", "ADDRESSED"),
            ChecklistItem("ISSUE-002", "T2", "R2", "ADDRESSED"),
        ]
        coverage = calculate_coverage(items)
        assert coverage.total == 2
        assert coverage.addressed == 2
        assert coverage.rejected == 0
        assert coverage.deferred == 0
        assert coverage.not_applicable == 0
        assert coverage.invalid == 0

    def test_coverage_mixed_statuses(self) -> None:
        """Test coverage with mixed status values."""
        items = [
            ChecklistItem("ISSUE-001", "T1", "R1", "ADDRESSED"),
            ChecklistItem("ISSUE-002", "T2", "R2", "REJECTED"),
            ChecklistItem("ISSUE-003", "T3", "R3", "DEFERRED"),
            ChecklistItem("ISSUE-004", "T4", "R4", "NOT_APPLICABLE"),
        ]
        coverage = calculate_coverage(items)
        assert coverage.total == 4
        assert coverage.addressed == 1
        assert coverage.rejected == 1
        assert coverage.deferred == 1
        assert coverage.not_applicable == 1
        assert coverage.invalid == 0

    def test_coverage_with_invalid_status(self) -> None:
        """Test coverage with invalid status values."""
        items = [
            ChecklistItem("ISSUE-001", "T1", "R1", "ADDRESSED"),
            ChecklistItem("ISSUE-002", "T2", "R2", "UNKNOWN"),
            ChecklistItem("ISSUE-003", "T3", "R3", "INVALID"),
        ]
        coverage = calculate_coverage(items)
        assert coverage.total == 3
        assert coverage.addressed == 1
        assert coverage.invalid == 2

    def test_coverage_empty_list(self) -> None:
        """Test coverage with empty list."""
        coverage = calculate_coverage([])
        assert coverage.total == 0

    def test_coverage_case_insensitive(self) -> None:
        """Test coverage handles case-insensitive status."""
        items = [
            ChecklistItem("ISSUE-001", "T1", "R1", "addressed"),
            ChecklistItem("ISSUE-002", "T2", "R2", "Rejected"),
        ]
        coverage = calculate_coverage(items)
        assert coverage.addressed == 1
        assert coverage.rejected == 1


class TestChecklistCoverage:
    """Tests for ChecklistCoverage dataclass."""

    def test_summary_all_addressed(self) -> None:
        """Test summary with all addressed items."""
        coverage = ChecklistCoverage(
            total=3, addressed=3, rejected=0, deferred=0, not_applicable=0, invalid=0
        )
        assert "3 addressed" in coverage.summary()
        assert "total: 3" in coverage.summary()

    def test_summary_mixed(self) -> None:
        """Test summary with mixed statuses."""
        coverage = ChecklistCoverage(
            total=5, addressed=2, rejected=1, deferred=1, not_applicable=1, invalid=0
        )
        summary = coverage.summary()
        assert "2 addressed" in summary
        assert "1 rejected" in summary
        assert "1 deferred" in summary
        assert "1 N/A" in summary

    def test_summary_with_invalid(self) -> None:
        """Test summary includes invalid count."""
        coverage = ChecklistCoverage(
            total=3, addressed=1, rejected=0, deferred=0, not_applicable=0, invalid=2
        )
        assert "2 invalid" in coverage.summary()

    def test_summary_empty(self) -> None:
        """Test summary with no items."""
        coverage = ChecklistCoverage(
            total=0, addressed=0, rejected=0, deferred=0, not_applicable=0, invalid=0
        )
        assert coverage.summary() == "No checklist items found"


class TestValidChecklistStatuses:
    """Tests for VALID_CHECKLIST_STATUSES constant."""

    def test_contains_all_valid_statuses(self) -> None:
        """Test all expected statuses are in the set."""
        assert "ADDRESSED" in VALID_CHECKLIST_STATUSES
        assert "REJECTED" in VALID_CHECKLIST_STATUSES
        assert "DEFERRED" in VALID_CHECKLIST_STATUSES
        assert "NOT_APPLICABLE" in VALID_CHECKLIST_STATUSES

    def test_exactly_four_statuses(self) -> None:
        """Test exactly four valid statuses exist."""
        assert len(VALID_CHECKLIST_STATUSES) == 4

import pytest
from pydantic import ValidationError
from app.models.review import (
    ReviewCategory,
    ReviewSeverity,
    ReviewFinding,
    StructuredReview,
)
from app.services.review_renderer import render_review_markdown


def test_structured_review_valid_creation():
    """Tests creation of a valid StructuredReview instance."""
    finding = ReviewFinding(
        title="Unbound variable",
        category=ReviewCategory.BUG_RISK,
        severity=ReviewSeverity.HIGH,
        file="app/main.py",
        line=15,
        description="Variable x is used before assignment.",
        suggested_fix="x = 0"
    )
    review = StructuredReview(
        summary="PR adds feature with minor bug risk.",
        overall_rating=8,
        findings=[finding]
    )
    assert review.overall_rating == 8
    assert len(review.findings) == 1
    assert review.findings[0].category == ReviewCategory.BUG_RISK


def test_overall_rating_lower_bound_validation():
    """Tests that overall_rating < 1 raises ValidationError."""
    with pytest.raises(ValidationError):
        StructuredReview(summary="Invalid rating", overall_rating=0, findings=[])


def test_overall_rating_upper_bound_validation():
    """Tests that overall_rating > 10 raises ValidationError."""
    with pytest.raises(ValidationError):
        StructuredReview(summary="Invalid rating", overall_rating=11, findings=[])


def test_category_enum_validation():
    """Tests that an invalid category string raises ValidationError."""
    with pytest.raises(ValidationError):
        ReviewFinding(
            title="Title",
            category="invalid_category",  # type: ignore
            severity=ReviewSeverity.LOW,
            description="Desc"
        )


def test_severity_enum_validation():
    """Tests that an invalid severity string raises ValidationError."""
    with pytest.raises(ValidationError):
        ReviewFinding(
            title="Title",
            category=ReviewCategory.SECURITY,
            severity="extreme",  # type: ignore
            description="Desc"
        )


def test_optional_file_and_line_fields():
    """Tests that file and line fields are optional."""
    finding = ReviewFinding(
        title="General advice",
        category=ReviewCategory.BEST_PRACTICE,
        severity=ReviewSeverity.INFO,
        description="Consider adding docstrings."
    )
    assert finding.file is None
    assert finding.line is None


def test_empty_findings_list():
    """Tests a StructuredReview with an empty findings array."""
    review = StructuredReview(
        summary="Clean PR without issues.",
        overall_rating=10,
        findings=[]
    )
    assert review.overall_rating == 10
    assert review.findings == []


def test_markdown_renderer_category_sections_and_score():
    """Tests that render_review_markdown produces expected sections and rating."""
    finding = ReviewFinding(
        title="Hardcoded Secret",
        category=ReviewCategory.SECURITY,
        severity=ReviewSeverity.CRITICAL,
        file="app/config.py",
        line=10,
        description="Secret key is hardcoded.",
        suggested_fix="Use os.getenv('SECRET')"
    )
    review = StructuredReview(
        summary="Security concern identified.",
        overall_rating=4,
        findings=[finding]
    )

    markdown = render_review_markdown(review)

    assert "# CodeSage AI Review" in markdown
    assert "## Summary" in markdown
    assert "Security concern identified." in markdown
    assert "## Overall Rating" in markdown
    assert "**4/10**" in markdown
    assert "## Security Issues" in markdown
    assert "🚨 [CRITICAL] Hardcoded Secret" in markdown
    assert "**File:** `app/config.py` • **Line:** `10`" in markdown
    assert "Suggested Fix:" in markdown


def test_markdown_renderer_handles_missing_file_and_line():
    """Tests rendering of a finding without file or line attributes."""
    finding = ReviewFinding(
        title="Global architectural note",
        category=ReviewCategory.BEST_PRACTICE,
        severity=ReviewSeverity.INFO,
        description="Ensure all modules are exported."
    )
    review = StructuredReview(
        summary="Architecture note.",
        overall_rating=9,
        findings=[finding]
    )

    markdown = render_review_markdown(review)

    assert "ℹ️ [INFO] Global architectural note" in markdown
    assert "**File:**" not in markdown


def test_markdown_renderer_handles_empty_findings():
    """Tests that categories with no findings display 'No issues detected.'."""
    review = StructuredReview(
        summary="Flawless code changes.",
        overall_rating=10,
        findings=[]
    )

    markdown = render_review_markdown(review)

    assert "## Security Issues" in markdown
    assert "No issues detected." in markdown
    assert "**10/10**" in markdown

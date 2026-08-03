import re
from typing import List, Dict, Optional
from app.models.review import StructuredReview, ReviewCategory, ReviewSeverity

# Centralized header marker for identifying CodeSage review comments
CODESAGE_REVIEW_MARKER = "# CodeSage AI Review"

# Category display metadata mapping
CATEGORY_HEADERS: Dict[ReviewCategory, str] = {
    ReviewCategory.SECURITY: "## Security Issues",
    ReviewCategory.BUG_RISK: "## Bug Risks",
    ReviewCategory.CODE_QUALITY: "## Code Quality",
    ReviewCategory.PERFORMANCE: "## Performance Concerns",
    ReviewCategory.BEST_PRACTICE: "## Best Practice Suggestions",
}

# Severity badge indicators
SEVERITY_BADGES: Dict[ReviewSeverity, str] = {
    ReviewSeverity.CRITICAL: "🚨 [CRITICAL]",
    ReviewSeverity.HIGH: "⚠️ [HIGH]",
    ReviewSeverity.MEDIUM: "🟡 [MEDIUM]",
    ReviewSeverity.LOW: "🔹 [LOW]",
    ReviewSeverity.INFO: "ℹ️ [INFO]",
}


def is_codesage_review_comment(body: str) -> bool:
    """
    Determines whether a comment body originated from CodeSage AI.
    Checks for the canonical header marker.
    """
    if not body:
        return False
    return CODESAGE_REVIEW_MARKER in body


def extract_overall_rating_from_markdown(body: str) -> Optional[int]:
    """
    Attempts to extract the numeric overall score rating (1 to 10) from a CodeSage review Markdown comment.
    Looks for standard block format: '## Overall Rating\\n**8/10**' or '**X/10**'.
    Returns None if format does not match cleanly or is out of bounds.
    """
    if not body or not is_codesage_review_comment(body):
        return None

    # Search for bold rating format e.g. **8/10** or **10/10**
    match = re.search(r"\*\*(\d{1,2})/10\*\*", body)
    if not match:
        match = re.search(r"Overall Rating.*?\b(\d{1,2})/10\b", body, re.IGNORECASE)

    if match:
        try:
            score = int(match.group(1))
            if 1 <= score <= 10:
                return score
        except ValueError:
            pass

    return None


def render_review_markdown(review: StructuredReview) -> str:
    """
    Converts a strongly-typed StructuredReview instance into a clean, professional GitHub Markdown comment string.

    Args:
        review: Validated StructuredReview Pydantic model.

    Returns:
        Formatted GitHub Markdown string.
    """
    sections = [
        f"{CODESAGE_REVIEW_MARKER}\n",
        f"## Summary\n{review.summary.strip()}\n",
        f"## Overall Rating\n**{review.overall_rating}/10**\n"
    ]

    # Group findings by category
    findings_by_category: Dict[ReviewCategory, List] = {cat: [] for cat in ReviewCategory}
    for finding in review.findings:
        findings_by_category[finding.category].append(finding)

    # Render each standard review section
    for category in ReviewCategory:
        header = CATEGORY_HEADERS[category]
        cat_findings = findings_by_category[category]

        sections.append(header)

        if not cat_findings:
            sections.append("No issues detected.\n")
            continue

        for finding in cat_findings:
            badge = SEVERITY_BADGES.get(finding.severity, f"[{finding.severity.value.upper()}]")
            item_markdown = [f"### {badge} {finding.title.strip()}"]

            # File and Line location metadata
            location_parts = []
            if finding.file:
                location_parts.append(f"**File:** `{finding.file.strip()}`")
            if finding.line is not None:
                location_parts.append(f"**Line:** `{finding.line}`")

            if location_parts:
                item_markdown.append(" • ".join(location_parts))

            item_markdown.append(f"\n{finding.description.strip()}\n")

            if finding.suggested_fix:
                fix_text = finding.suggested_fix.strip()
                if not fix_text.startswith("```"):
                    fix_markdown = f"**Suggested Fix:**\n```\n{fix_text}\n```"
                else:
                    fix_markdown = f"**Suggested Fix:**\n{fix_text}"
                item_markdown.append(fix_markdown)

            sections.append("\n".join(item_markdown) + "\n")

    return "\n".join(sections).strip()

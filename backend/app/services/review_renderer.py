from typing import List, Dict
from app.models.review import StructuredReview, ReviewCategory, ReviewSeverity

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


def render_review_markdown(review: StructuredReview) -> str:
    """
    Converts a strongly-typed StructuredReview instance into a clean, professional GitHub Markdown comment string.

    Args:
        review: Validated StructuredReview Pydantic model.

    Returns:
        Formatted GitHub Markdown string.
    """
    sections = [
        "# CodeSage AI Review\n",
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

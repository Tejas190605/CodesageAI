import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from app.services.review_rules.base import RuleResult
from app.services.review_decision import compute_review_decision

logger = logging.getLogger("codesage.github_review_publisher")

MAX_INLINE_COMMENTS_BUDGET = 10


def format_suggested_change(suggested_fix: str) -> str:
    """Formats a bounded code replacement as a GitHub Markdown suggested change block."""
    clean_fix = suggested_fix.strip()
    if clean_fix.startswith("```"):
        return clean_fix
    return f"```suggestion\n{clean_fix}\n```"


def build_pr_review_summary(
    review_decision: Dict[str, Any],
    rule_results: List[RuleResult],
    rag_citations: Optional[List[str]] = None,
    overall_rating: int = 9
) -> str:
    """
    Generates a structured, actionable Pull Request Review Summary for GitHub.
    Include Risk Assessment, Policy Results, Security Findings, RAG Citations, and Review Decision.
    """
    event = review_decision.get("event", "COMMENT")
    reason = review_decision.get("reason", "")
    counts = review_decision.get("summary_counts", {})

    status_badge = "✅ PASS" if event in ("APPROVE", "COMMENT") and counts.get("critical", 0) == 0 else "❌ BLOCKING ISSUES"

    sections = [
        "# CodeSage AI — Pull Request Review",
        f"**Decision:** `{event}` • **Policy Status:** {status_badge}",
        f"**Overall Code Quality Rating:** **{overall_rating}/10**\n",
        "## Policy Evaluation Summary",
        f"- **Critical:** {counts.get('critical', 0)}",
        f"- **High:** {counts.get('high', 0)}",
        f"- **Medium:** {counts.get('medium', 0)}",
        f"- **Low / Info:** {counts.get('low', 0)}\n",
        f"**Summary Assessment:** {reason}\n"
    ]

    if rag_citations:
        sections.append("## Repository Context Used (RAG)")
        for cit in rag_citations[:5]:
            sections.append(f"- `{cit}`")
        sections.append("")

    if rule_results:
        sections.append("## Key Findings & Suggested Actions")
        for idx, r in enumerate(rule_results[:10], start=1):
            badge = "🚨" if r.severity == "critical" else ("⚠️" if r.severity == "high" else "🔹")
            loc = f"`{r.file_path}:L{r.start_line}`" if r.file_path and r.start_line else "Global"
            item = f"{idx}. {badge} **[{r.severity.upper()}]** ({r.rule_key}) in {loc}\n   {r.message}"
            if r.evidence:
                item += f"\n   > `Evidence:` {r.evidence}"
            sections.append(item)

    return "\n".join(sections).strip()


def prepare_inline_comments(
    rule_results: List[RuleResult],
    changed_files: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[RuleResult]]:
    """
    Validates inline comments against PR changed file bounds:
    - Verifies file exists in changed PR diff.
    - Validates line number belongs to valid changed patch range.
    - Applies comment budget budget limits (max 10 inline comments prioritized by severity).
    - Unplaceable findings fall back to review summary.
    """
    valid_files_map: Dict[str, Set[int]] = {}

    for f in changed_files:
        filename = f.get("filename", "")
        patch = f.get("patch", "")
        if not filename or not patch:
            continue

        changed_lines: Set[int] = set()
        current_line = 1
        for line in patch.splitlines():
            if line.startswith("@@"):
                import re
                m = re.search(r"\+(\d+)", line)
                if m:
                    current_line = int(m.group(1))
                continue
            if line.startswith("+") and not line.startswith("+++"):
                changed_lines.add(current_line)
                current_line += 1
            elif not line.startswith("-"):
                current_line += 1

        valid_files_map[filename] = changed_lines

    # Sort results by severity priority: critical > high > medium > low > info
    severity_rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    sorted_results = sorted(rule_results, key=lambda x: severity_rank.get(x.severity, 1), reverse=True)

    inline_comments: List[Dict[str, Any]] = []
    fallback_summary_findings: List[RuleResult] = []

    for r in sorted_results:
        if len(inline_comments) >= MAX_INLINE_COMMENTS_BUDGET:
            fallback_summary_findings.append(r)
            continue

        if r.file_path and r.file_path in valid_files_map and r.start_line:
            target_line = r.start_line
            # Check if target line is within changed diff patch bounds
            if target_line in valid_files_map[r.file_path]:
                comment_body = f"**[{r.severity.upper()}]** {r.message}"
                if r.suggested_fix:
                    comment_body += f"\n\n{format_suggested_change(r.suggested_fix)}"

                inline_comments.append({
                    "path": r.file_path,
                    "line": target_line,
                    "side": "RIGHT",
                    "body": comment_body
                })
            else:
                fallback_summary_findings.append(r)
        else:
            fallback_summary_findings.append(r)

    return inline_comments, fallback_summary_findings

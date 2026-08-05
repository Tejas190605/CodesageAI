import logging
from typing import List, Dict, Any
from app.services.review_rules.base import RuleResult

logger = logging.getLogger("codesage.review_decision")


def compute_review_decision(
    rule_results: List[RuleResult],
    allow_request_changes: bool = False,
    allow_approve: bool = False
) -> Dict[str, Any]:
    """
    Computes overall PR review decision (APPROVE, COMMENT, REQUEST_CHANGES):
    - Default behavior is non-blocking (COMMENT).
    - If critical/high findings exist and allow_request_changes=True -> REQUEST_CHANGES.
    - If no warnings or failures exist and allow_approve=True -> APPROVE.
    """
    critical_count = sum(1 for r in rule_results if r.severity == "critical")
    high_count = sum(1 for r in rule_results if r.severity == "high")
    medium_count = sum(1 for r in rule_results if r.severity == "medium")
    low_count = sum(1 for r in rule_results if r.severity in ("low", "info"))

    if (critical_count > 0 or high_count > 0) and allow_request_changes:
        decision = "REQUEST_CHANGES"
        reason = f"Blocking issues detected ({critical_count} critical, {high_count} high)."
    elif len(rule_results) == 0 and allow_approve:
        decision = "APPROVE"
        reason = "Clean automated review — no policy issues detected."
    else:
        decision = "COMMENT"
        reason = f"Automated review completed with {len(rule_results)} feedback item(s)."

    return {
        "event": decision,
        "reason": reason,
        "summary_counts": {
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "total": len(rule_results)
        }
    }

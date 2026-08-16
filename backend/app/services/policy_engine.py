import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.db import PolicyEvaluation, RuleEvaluation
from app.models.review import StructuredReview, ReviewFinding
from app.services.policy_config import get_effective_policy
from app.services.review_rules import (
    RuleResult,
    evaluate_debug_code_rule,
    evaluate_secrets_rule,
    evaluate_dependency_rule,
    evaluate_testing_rule,
)

logger = logging.getLogger("codesage.policy_engine")

SEVERITY_ORDER = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1
}


def is_path_ignored(file_path: str, ignore_paths: List[str]) -> bool:
    """Checks if a file path matches explicit ignore glob patterns."""
    if not file_path:
        return False
    for pat in ignore_paths:
        clean_pat = pat.replace("**", "").replace("*", "")
        if clean_pat and clean_pat in file_path:
            return True
    return False


def calculate_finding_fingerprint(rule_key: str, file_path: str, line: int, message: str) -> str:
    """Generates a SHA-256 fingerprint to deduplicate identical findings."""
    raw = f"{rule_key}:{file_path or 'global'}:{line or 0}:{message.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def evaluate_policy_for_pr(
    db: Session,
    review_id: int,
    files: List[Dict[str, Any]],
    structured_review: Optional[StructuredReview] = None,
    yaml_config_str: Optional[str] = None
) -> Tuple[PolicyEvaluation, List[RuleResult]]:
    """
    Executes policy engine analysis for a Pull Request:
    1. Resolves effective policy hierarchy (.codesage.yml / DB / System defaults).
    2. Runs deterministic checks (debug code, secrets, dependencies, test coverage).
    3. Merges AI findings, validating rule categories and severity mappings.
    4. Deduplicates findings using SHA-256 fingerprints.
    5. Applies suppression controls and persists PolicyEvaluation snapshot.
    """
    effective_policy = get_effective_policy(yaml_config_str=yaml_config_str)
    rules_cfg = effective_policy["rules"]
    ignore_paths = effective_policy["ignore_paths"]
    ignore_rules = effective_policy["ignore_rules"]

    all_rule_results: List[RuleResult] = []

    # 1. Deterministic Checks
    if "debug-code" not in ignore_rules:
        all_rule_results.extend(evaluate_debug_code_rule(files, rules_cfg.get("debug-code", {})))
    if "hardcoded-secrets" not in ignore_rules:
        all_rule_results.extend(evaluate_secrets_rule(files, rules_cfg.get("hardcoded-secrets", {})))
    if "dependency-changes" not in ignore_rules:
        all_rule_results.extend(evaluate_dependency_rule(files, rules_cfg.get("dependency-changes", {})))
    if "missing-tests" not in ignore_rules:
        all_rule_results.extend(evaluate_testing_rule(files, rules_cfg.get("missing-tests", {})))

    # 2. Merge AI StructuredReview Findings
    if structured_review and structured_review.findings:
        for f in structured_review.findings:
            cat_str = f.category.value if hasattr(f.category, "value") else str(f.category)
            sev_str = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            rule_key = cat_str if cat_str in rules_cfg else "owasp-security"
            if rule_key in ignore_rules:
                continue

            all_rule_results.append(RuleResult(
                rule_key=rule_key,
                status="fail" if sev_str in ("critical", "high") else "warning",
                severity=sev_str,
                message=f.description or f.title,
                file_path=f.file,
                start_line=f.line,
                end_line=f.line,
                evidence=None,
                suggested_fix=f.suggested_fix
            ))

    # 3. Path Suppression & Finding Deduplication
    filtered_results: List[RuleResult] = []
    seen_fingerprints = set()

    for r in all_rule_results:
        if r.file_path and is_path_ignored(r.file_path, ignore_paths):
            continue

        fp = calculate_finding_fingerprint(r.rule_key, r.file_path or "", r.start_line or 0, r.message)
        if fp in seen_fingerprints:
            continue

        seen_fingerprints.add(fp)
        filtered_results.append(r)

    # 4. Count Warnings, Failures, and Blocking Issues
    warning_cnt = sum(1 for r in filtered_results if r.status == "warning")
    failure_cnt = sum(1 for r in filtered_results if r.status == "fail")
    blocking_cnt = sum(1 for r in filtered_results if r.severity in ("critical", "high"))
    passed = (blocking_cnt == 0)

    # 5. Persist Evaluation Snapshot in Database
    evaluation_rec = PolicyEvaluation(
        review_id=review_id,
        passed=passed,
        warning_count=warning_cnt,
        failure_count=failure_cnt,
        blocking_count=blocking_cnt
    )
    db.add(evaluation_rec)
    db.commit()
    db.refresh(evaluation_rec)

    for r in filtered_results:
        rule_eval_rec = RuleEvaluation(
            policy_evaluation_id=evaluation_rec.id,
            rule_key=r.rule_key,
            status=r.status,
            message=r.message,
            file_path=r.file_path,
            start_line=r.start_line,
            end_line=r.end_line,
            metadata_json={"severity": r.severity, "evidence": r.evidence, "suggested_fix": r.suggested_fix}
        )
        db.add(rule_eval_rec)

    db.commit()
    logger.info(f"Completed policy evaluation for review_id={review_id}: passed={passed}, warnings={warning_cnt}, failures={failure_cnt}, blocking={blocking_cnt}.")
    return evaluation_rec, filtered_results

from typing import List, Dict, Any
from app.services.review_rules.base import RuleResult


def evaluate_testing_rule(files: List[Dict[str, Any]], config: Dict[str, Any]) -> List[RuleResult]:
    """Warns when core production logic is modified without accompanying test file updates."""
    results: List[RuleResult] = []
    if not config.get("enabled", True):
        return results

    severity = config.get("severity", "medium")

    prod_files_changed = []
    test_files_changed = []

    for f in files:
        filename = f.get("filename", "")
        if "test" in filename.lower() or "spec" in filename.lower():
            test_files_changed.append(filename)
        elif filename.endswith((".py", ".ts", ".js", ".go", ".java")):
            prod_files_changed.append(filename)

    if prod_files_changed and not test_files_changed:
        results.append(RuleResult(
            rule_key="missing-tests",
            status="warning",
            severity=severity,
            message=f"{len(prod_files_changed)} production source file(s) modified without corresponding test file updates.",
            file_path=prod_files_changed[0],
            start_line=1,
            end_line=1,
            evidence=f"Production changes in {', '.join(prod_files_changed[:3])} lack test updates."
        ))

    return results

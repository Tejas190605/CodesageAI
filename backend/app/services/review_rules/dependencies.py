from typing import List, Dict, Any
from app.services.review_rules.base import RuleResult

MANIFEST_FILES = {
    "requirements.txt", "pyproject.toml", "Pipfile", "package.json",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "go.mod", "Cargo.toml"
}


def evaluate_dependency_rule(files: List[Dict[str, Any]], config: Dict[str, Any]) -> List[RuleResult]:
    """Detects dependency additions, version changes, and lockfile updates."""
    results: List[RuleResult] = []
    if not config.get("enabled", True):
        return results

    severity = config.get("severity", "info")

    for f in files:
        filename = f.get("filename", "")
        basename = filename.split("/")[-1]

        if basename in MANIFEST_FILES:
            status_kind = f.get("status", "modified")
            results.append(RuleResult(
                rule_key="dependency-changes",
                status="warning" if status_kind == "added" else "pass",
                severity=severity,
                message=f"Project dependency manifest change detected in '{filename}' (Status: {status_kind}).",
                file_path=filename,
                start_line=1,
                end_line=1,
                evidence=f"Manifest file {filename} was {status_kind}."
            ))

    return results

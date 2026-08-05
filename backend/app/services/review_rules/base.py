from typing import Optional, Dict, Any


class RuleResult:
    """Represents a deterministic or AI policy evaluation finding."""

    def __init__(
        self,
        rule_key: str,
        status: str,  # pass, warning, fail, skipped
        severity: str,  # critical, high, medium, low, info
        message: str,
        file_path: Optional[str] = None,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        evidence: Optional[str] = None,
        suggested_fix: Optional[str] = None
    ):
        self.rule_key = rule_key
        self.status = status
        self.severity = severity
        self.message = message
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.evidence = evidence
        self.suggested_fix = suggested_fix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_key": self.rule_key,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }

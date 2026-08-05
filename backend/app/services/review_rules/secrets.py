import re
from typing import List, Dict, Any
from app.services.review_rules.base import RuleResult

SECRET_PATTERNS = [
    (re.compile(r"ghp_[a-zA-Z0-9]{20,}"), "GitHub Personal Access Token"),
    (re.compile(r"gho_[a-zA-Z0-9]{20,}"), "GitHub OAuth Access Token"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "API Secret Key"),
    (re.compile(r"sk_live_[a-zA-Z0-9]{20,}"), "Live Stripe/Provider API Key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "Private Key Header"),
    (re.compile(r"(?:password|secret|api_key|access_token)\s*=\s*['\"][a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}]{8,}['\"]", re.IGNORECASE), "Hardcoded Credentials")
]


def redact_secret(text: str) -> str:
    """Redacts discovered secret strings for security compliance."""
    def _repl(match):
        val = match.group(0)
        if len(val) <= 8:
            return "********"
        return val[:4] + "*" * (len(val) - 4)

    redacted = text
    for pattern, _ in SECRET_PATTERNS:
        redacted = pattern.sub(_repl, redacted)
    return redacted


def evaluate_secrets_rule(files: List[Dict[str, Any]], config: Dict[str, Any]) -> List[RuleResult]:
    """Detects exposed API tokens, private keys, and hardcoded credentials."""
    results: List[RuleResult] = []
    if not config.get("enabled", True):
        return results

    severity = config.get("severity", "critical")

    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch", "")
        if not patch:
            continue

        lines = patch.splitlines()
        current_line = 1

        for line in lines:
            if line.startswith("@@"):
                m = re.search(r"\+(\d+)", line)
                if m:
                    current_line = int(m.group(1))
                continue

            if line.startswith("+") and not line.startswith("+++"):
                line_content = line[1:].strip()
                for pattern, secret_type in SECRET_PATTERNS:
                    if pattern.search(line_content):
                        redacted_evidence = redact_secret(line_content)
                        results.append(RuleResult(
                            rule_key="hardcoded-secrets",
                            status="fail",
                            severity=severity,
                            message=f"Hardcoded secret detected ({secret_type}). Immediate revocation required.",
                            file_path=filename,
                            start_line=current_line,
                            end_line=current_line,
                            evidence=redacted_evidence
                        ))
                        break
                current_line += 1
            elif not line.startswith("-"):
                current_line += 1

    return results

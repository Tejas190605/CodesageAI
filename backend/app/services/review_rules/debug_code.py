import re
from typing import List, Dict, Any
from app.services.review_rules.base import RuleResult


def evaluate_debug_code_rule(files: List[Dict[str, Any]], config: Dict[str, Any]) -> List[RuleResult]:
    """Detects leftover debug statements (print, breakpoint, console.log, debugger)."""
    results: List[RuleResult] = []
    if not config.get("enabled", True):
        return results

    severity = config.get("severity", "low")

    # Regular expressions for added debug lines in git patches
    py_debug_pattern = re.compile(r"^\+\s*(print\(|breakpoint\(\))")
    js_debug_pattern = re.compile(r"^\+\s*(console\.log\(|debugger;)")

    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch", "")
        if not patch:
            continue

        lines = patch.splitlines()
        current_line = 1

        for line in lines:
            if line.startswith("@@"):
                # Parse line numbers from hunk header @@ -old,count +new,count @@
                m = re.search(r"\+(\d+)", line)
                if m:
                    current_line = int(m.group(1))
                continue

            if line.startswith("+") and not line.startswith("+++"):
                if filename.endswith(".py") and py_debug_pattern.search(line):
                    results.append(RuleResult(
                        rule_key="debug-code",
                        status="warning",
                        severity=severity,
                        message="Leftover Python debug statement detected (print/breakpoint).",
                        file_path=filename,
                        start_line=current_line,
                        end_line=current_line,
                        evidence=line[1:].strip()
                    ))
                elif filename.endswith((".js", ".ts", ".jsx", ".tsx")) and js_debug_pattern.search(line):
                    results.append(RuleResult(
                        rule_key="debug-code",
                        status="warning",
                        severity=severity,
                        message="Leftover JavaScript/TypeScript debug statement detected (console.log/debugger).",
                        file_path=filename,
                        start_line=current_line,
                        end_line=current_line,
                        evidence=line[1:].strip()
                    ))
                current_line += 1
            elif not line.startswith("-"):
                current_line += 1

    return results

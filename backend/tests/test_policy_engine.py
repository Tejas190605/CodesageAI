import pytest
from app.services.policy_config import parse_codesage_yml, get_effective_policy
from app.services.review_rules import (
    RuleResult,
    evaluate_debug_code_rule,
    evaluate_secrets_rule,
    evaluate_dependency_rule,
    evaluate_testing_rule,
)
from app.services.review_rules.secrets import redact_secret
from app.services.policy_engine import (
    calculate_finding_fingerprint,
    is_path_ignored,
    evaluate_policy_for_pr,
)
from app.services.review_decision import compute_review_decision
from app.services.github_review_publisher import (
    format_suggested_change,
    build_pr_review_summary,
    prepare_inline_comments,
)


def test_codesage_yml_safe_parsing():
    """Tests secure parsing of .codesage.yml configurations."""
    yaml_text = """
version: 1
review:
  depth: thorough
rules:
  debug-code:
    enabled: false
ignore:
  paths:
    - vendor/**
  rules:
    - missing-tests
"""
    cfg = parse_codesage_yml(yaml_text)
    assert cfg.version == 1
    assert cfg.depth == "thorough"
    assert "vendor/**" in cfg.ignore_paths
    assert "missing-tests" in cfg.ignore_rules
    assert cfg.rules["debug-code"]["enabled"] is False

    # Test invalid / empty YAML safety
    empty_cfg = parse_codesage_yml("invalid: : : yaml")
    assert empty_cfg.version == 1


def test_policy_precedence_resolution():
    """Tests Policy Hierarchy: Repository Config -> Org Overrides -> System Defaults."""
    yaml_text = "rules:\n  hardcoded-secrets:\n    severity: critical\n"
    org_overrides = {"rules": {"debug-code": {"severity": "high"}}}

    effective = get_effective_policy(yaml_config_str=yaml_text, org_overrides=org_overrides)
    rules = effective["rules"]

    assert rules["hardcoded-secrets"]["severity"] == "critical"
    assert rules["debug-code"]["severity"] == "high"


def test_deterministic_debug_code_rule():
    """Tests debug statement detection for Python and JS/TS."""
    files = [
        {
            "filename": "app/main.py",
            "patch": "@@ -10,3 +10,4 @@\n def run():\n+    print('DEBUGGING')\n+    breakpoint()\n"
        },
        {
            "filename": "src/app.ts",
            "patch": "@@ -1,2 +1,3 @@\n+console.log('test')\n"
        }
    ]
    results = evaluate_debug_code_rule(files, {"enabled": True, "severity": "low"})
    assert len(results) >= 2
    assert any("print" in r.message or "breakpoint" in r.message for r in results)


test_secret_redaction_cases = [
    ("api_key = 'TEST_SECRET_API_KEY_1234567890'", "api_************************************"),
    ("access_token = 'TEST_SECRET_ACCESS_TOKEN_1234567890'", "acce*****************************************")
]

@pytest.mark.parametrize("input_sec, expected_prefix", test_secret_redaction_cases)
def test_secret_detection_and_redaction(input_sec, expected_prefix):
    """Tests secret pattern detection and safe redaction helper."""
    redacted = redact_secret(input_sec)
    assert input_sec not in redacted
    assert redacted.startswith(expected_prefix[:4])


def test_deterministic_secrets_rule():
    """Tests hardcoded secret detection in file diff patches."""
    files = [
        {
            "filename": "config/settings.py",
            "patch": "@@ -1,2 +1,3 @@\n+API_KEY = 'TEST_SECRET_API_KEY_1234567890'\n"
        }
    ]
    results = evaluate_secrets_rule(files, {"enabled": True, "severity": "critical"})
    assert len(results) == 1
    assert results[0].severity == "critical"
    assert "TEST_SECRET_API_KEY_1234567890" not in results[0].evidence


def test_dependency_and_testing_rules():
    """Tests dependency manifest detection and test coverage heuristics."""
    files = [
        {"filename": "requirements.txt", "status": "modified", "patch": "@@ -1 +1 @@\n+fastapi==0.136.1\n"},
        {"filename": "app/auth.py", "status": "modified", "patch": "@@ -1 +1 @@\n+def login(): pass\n"}
    ]

    dep_res = evaluate_dependency_rule(files, {"enabled": True, "severity": "info"})
    assert len(dep_res) == 1

    test_res = evaluate_testing_rule(files, {"enabled": True, "severity": "medium"})
    assert len(test_res) == 1
    assert "production source file" in test_res[0].message


def test_finding_deduplication_and_suppression():
    """Tests fingerprint deduplication and path suppression controls."""
    assert is_path_ignored("vendor/lib/util.py", ["vendor/**"]) is True
    assert is_path_ignored("app/main.py", ["vendor/**"]) is False

    fp1 = calculate_finding_fingerprint("debug-code", "app/main.py", 12, "Debug statement")
    fp2 = calculate_finding_fingerprint("debug-code", "app/main.py", 12, "Debug statement")
    assert fp1 == fp2


def test_review_decision_engine():
    """Tests PR review decision logic (APPROVE, COMMENT, REQUEST_CHANGES)."""
    # 1. Non-blocking default behavior
    res1 = [RuleResult("debug-code", "warning", "low", "Debug print")]
    dec1 = compute_review_decision(res1, allow_request_changes=False)
    assert dec1["event"] == "COMMENT"

    # 2. Critical blocking finding
    res2 = [RuleResult("hardcoded-secrets", "fail", "critical", "Secret exposed")]
    dec2 = compute_review_decision(res2, allow_request_changes=True)
    assert dec2["event"] == "REQUEST_CHANGES"

    # 3. Clean PR approval
    dec3 = compute_review_decision([], allow_approve=True)
    assert dec3["event"] == "APPROVE"


def test_github_review_publisher_and_inline_bounds():
    """Tests suggested changes markdown, review summary generation, and inline line bounds validation."""
    suggested = format_suggested_change("return True")
    assert "```suggestion" in suggested

    rule_results = [
        RuleResult("debug-code", "warning", "low", "Debug print", "app/main.py", 12)
    ]
    summary = build_pr_review_summary({"event": "COMMENT", "reason": "Passed"}, rule_results)
    assert "CodeSage AI" in summary
    assert "Debug print" in summary

    changed_files = [
        {"filename": "app/main.py", "patch": "@@ -10,10 +10,10 @@\n+line 10\n+line 11\n+line 12\n"}
    ]
    inlines, fallbacks = prepare_inline_comments(rule_results, changed_files)
    assert len(inlines) == 1
    assert inlines[0]["path"] == "app/main.py"
    assert inlines[0]["line"] == 12


def test_policy_rest_api_endpoints(client):
    """Tests policy listing and effective policy REST endpoints."""
    res1 = client.get("/api/policies")
    assert res1.status_code == 200

    res2 = client.get("/api/policies/effective/test-owner/test-repo")
    assert res2.status_code == 200
    assert "effective_policy" in res2.json()

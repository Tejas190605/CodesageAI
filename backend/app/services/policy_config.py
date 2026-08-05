import logging
import yaml
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("codesage.policy_config")

# Default System Policy Rules Configuration
DEFAULT_SYSTEM_RULES: Dict[str, Dict[str, Any]] = {
    "debug-code": {
        "enabled": True,
        "category": "code_quality",
        "severity": "low",
        "description": "Detects leftover debug print statements or debugger breakpoints."
    },
    "hardcoded-secrets": {
        "enabled": True,
        "category": "security",
        "severity": "critical",
        "description": "Detects exposed API tokens, private keys, or credential formats."
    },
    "missing-tests": {
        "enabled": True,
        "category": "best_practice",
        "severity": "medium",
        "description": "Warns when core production logic changes without accompanying test changes."
    },
    "dependency-changes": {
        "enabled": True,
        "category": "security",
        "severity": "info",
        "description": "Tracks new or modified dependencies in project manifests."
    },
    "owasp-security": {
        "enabled": True,
        "category": "security",
        "severity": "high",
        "description": "AI-assisted checks for OWASP Top 10 security misconfigurations & vulnerabilities."
    }
}


class CodeSageConfig(BaseModel):
    version: int = 1
    depth: str = "thorough"
    rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    ignore_paths: List[str] = Field(default_factory=list)
    ignore_rules: List[str] = Field(default_factory=list)


def parse_codesage_yml(yaml_content: str) -> CodeSageConfig:
    """
    Safely parses repository .codesage.yml configuration.
    Uses safe_load to prevent arbitrary code execution vulnerabilities.
    """
    if not yaml_content or not yaml_content.strip():
        return CodeSageConfig()

    try:
        raw_dict = yaml.safe_load(yaml_content)
        if not isinstance(raw_dict, dict):
            logger.warning("Invalid .codesage.yml content structure (not a dict). Using defaults.")
            return CodeSageConfig()

        review_opts = raw_dict.get("review", {})
        depth = review_opts.get("depth", "thorough") if isinstance(review_opts, dict) else "thorough"

        rules_opt = raw_dict.get("rules", {})
        ignore_opt = raw_dict.get("ignore", {})
        ignore_paths = ignore_opt.get("paths", []) if isinstance(ignore_opt, dict) else []
        ignore_rules = ignore_opt.get("rules", []) if isinstance(ignore_opt, dict) else []

        return CodeSageConfig(
            version=raw_dict.get("version", 1),
            depth=depth,
            rules=rules_opt if isinstance(rules_opt, dict) else {},
            ignore_paths=ignore_paths if isinstance(ignore_paths, list) else [],
            ignore_rules=ignore_rules if isinstance(ignore_rules, list) else []
        )
    except Exception as e:
        logger.error(f"Failed to parse .codesage.yml securely: {e}")
        return CodeSageConfig()


def get_effective_policy(
    yaml_config_str: Optional[str] = None,
    org_overrides: Optional[Dict[str, Any]] = None,
    repo_overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Resolves final deterministic policy hierarchy with strict precedence:
    Repository Configuration (.codesage.yml / DB) -> Organization Defaults -> System Defaults.
    """
    effective_rules = {k: dict(v) for k, v in DEFAULT_SYSTEM_RULES.items()}
    effective_ignore_paths: List[str] = []
    effective_ignore_rules: List[str] = []

    # 1. Apply Organization Overrides
    if org_overrides and "rules" in org_overrides:
        for r_key, r_cfg in org_overrides["rules"].items():
            if r_key in effective_rules and isinstance(r_cfg, dict):
                effective_rules[r_key].update(r_cfg)

    # 2. Parse .codesage.yml if present
    parsed_repo_yml = parse_codesage_yml(yaml_config_str or "")
    for r_key, r_cfg in parsed_repo_yml.rules.items():
        if r_key in effective_rules and isinstance(r_cfg, dict):
            effective_rules[r_key].update(r_cfg)

    effective_ignore_paths.extend(parsed_repo_yml.ignore_paths)
    effective_ignore_rules.extend(parsed_repo_yml.ignore_rules)

    # 3. Apply DB Repository Overrides if present
    if repo_overrides and "rules" in repo_overrides:
        for r_key, r_cfg in repo_overrides["rules"].items():
            if r_key in effective_rules and isinstance(r_cfg, dict):
                effective_rules[r_key].update(r_cfg)

    # Disable rules explicitly listed in ignore_rules
    for r_key in effective_ignore_rules:
        if r_key in effective_rules:
            effective_rules[r_key]["enabled"] = False

    return {
        "rules": effective_rules,
        "ignore_paths": effective_ignore_paths,
        "ignore_rules": effective_ignore_rules,
        "depth": parsed_repo_yml.depth
    }

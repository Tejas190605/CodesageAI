import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("codesage.prompt_service")


DEFAULT_SYSTEM_PROMPT = """You are CodeSage AI, a senior Staff Software Engineer performing code reviews on GitHub Pull Requests.
Evaluate for bug risks, security vulnerabilities, performance bottlenecks, and code style consistency.
Provide clear, actionable, structured JSON output."""

DEFAULT_PR_REVIEW_TEMPLATE = """Review the following Pull Request changes:
Repository: {repository}
Pull Request: #{pr_number} - {pr_title}

Changed Files Diff:
{diff}

Identify security, performance, correctness, and architecture findings."""


class PromptService:
    """Central Prompt Registry managing prompt templates, versioning, and variable rendering."""

    def __init__(self):
        self._templates: Dict[str, Dict[str, Any]] = {
            "default_pr_review": {
                "name": "default_pr_review",
                "version": "1.0.0",
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "template_text": DEFAULT_PR_REVIEW_TEMPLATE,
                "description": "Standard Staff Engineer AI Pull Request Code Review Prompt"
            }
        }

    def render_prompt(
        self,
        template_name: str = "default_pr_review",
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Renders template text with variables and returns formatted system and user prompts."""
        template = self._templates.get(template_name, self._templates["default_pr_review"])
        vars_dict = variables or {}

        try:
            rendered_user = template["template_text"].format(**vars_dict)
        except KeyError as e:
            logger.warning(f"Missing prompt template variable {e}. Falling back to raw str interpolation.")
            rendered_user = template["template_text"]

        return {
            "system_prompt": template["system_prompt"],
            "user_prompt": rendered_user,
            "version": template["version"]
        }


# Singleton Prompt Service Instance
prompt_service = PromptService()

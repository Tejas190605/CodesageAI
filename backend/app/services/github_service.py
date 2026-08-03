import logging
from typing import List, Dict, Any
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)
from app.config import settings

logger = logging.getLogger("codesage.github_service")


def _is_transient_github_error(exception: Exception) -> bool:
    """
    Returns True if an exception represents a transient network/server failure
    suitable for retry (e.g. timeout, connection error, HTTP 429, 500, 502, 503, 504).
    Returns False for permanent errors (e.g. 401 Unauthorized, 403 Forbidden, 404 Not Found).
    """
    if isinstance(exception, requests.HTTPError) and exception.response is not None:
        status_code = exception.response.status_code
        if status_code in (429, 500, 502, 503, 504):
            return True
        return False
    if isinstance(exception, (requests.Timeout, requests.ConnectionError)):
        return True
    return False


def _get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying GitHub API request (attempt {retry_state.attempt_number})..."
    ),
    reraise=True
)
def _fetch_pr_files_page(owner: str, repo: str, pr_number: int, page: int, per_page: int = 100) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    params = {"page": page, "per_page": per_page}

    response = requests.get(
        url,
        headers=_get_headers(),
        params=params,
        timeout=settings.GITHUB_API_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def get_pr_files(owner: str, repo: str, pr_number: int, max_pages: int = 10) -> List[Dict[str, str]]:
    """
    Fetches all changed files for a pull request using GitHub REST API pagination.

    Args:
        owner: Repository owner/organization name.
        repo: Repository name.
        pr_number: Pull request ID number.
        max_pages: Maximum number of pages to fetch defensively (default 10 pages / 1000 files).

    Returns:
        List of file dictionaries containing filename, status, and patch string.
    """
    all_files: List[Dict[str, str]] = []
    page = 1
    per_page = 100

    try:
        while page <= max_pages:
            logger.info(f"Fetching PR files for {owner}/{repo}#{pr_number} (page {page})...")
            github_files = _fetch_pr_files_page(owner, repo, pr_number, page=page, per_page=per_page)

            if not github_files:
                break

            for file in github_files:
                all_files.append({
                    "filename": file.get("filename", ""),
                    "status": file.get("status", "modified"),
                    "patch": file.get("patch", "No patch available")
                })

            if len(github_files) < per_page:
                # Reached last page
                break

            page += 1

        logger.info(f"Successfully retrieved {len(all_files)} total file entry/entries for PR #{pr_number}.")
        return all_files

    except Exception as e:
        logger.error(f"Failed to fetch PR files for {owner}/{repo}#{pr_number}: {e}")
        return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying GitHub PR comment posting (attempt {retry_state.attempt_number})..."
    ),
    reraise=True
)
def comment_on_pr(repo_full_name: str, pr_number: int, comment: str) -> int:
    """
    Posts a review comment to a GitHub Pull Request thread.

    Args:
        repo_full_name: Repository in 'owner/repo' format.
        pr_number: Pull request ID number.
        comment: Markdown comment content to post.

    Returns:
        HTTP status code (201 on success).
    """
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"

    try:
        response = requests.post(
            url,
            headers=_get_headers(),
            json={"body": comment},
            timeout=settings.GITHUB_API_TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"Successfully posted comment on PR {repo_full_name}#{pr_number} (HTTP {response.status_code}).")
        return response.status_code
    except Exception as e:
        logger.error(f"Failed to post comment on PR {repo_full_name}#{pr_number}: {e}")
        raise
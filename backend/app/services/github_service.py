import logging
from typing import List, Dict, Any, Optional
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)
from app.config import settings
from app.utils.circuit_breaker import github_api_circuit_breaker

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


def _get_headers(installation_id: Optional[int] = None) -> Dict[str, str]:
    token = None
    if installation_id:
        from app.services.github_app_service import get_installation_access_token
        token = get_installation_access_token(installation_id)
    if not token:
        # Check active installation in DB
        try:
            from app.database import SessionLocal
            from app.db_repositories.installation_repo import list_installations
            with SessionLocal() as db:
                insts = list_installations(db)
                if insts:
                    from app.services.github_app_service import get_installation_access_token
                    token = get_installation_access_token(insts[0].installation_id)
        except Exception:
            pass

    if not token:
        token = settings.GITHUB_TOKEN

    auth_header = f"token {token}" if token and (token.startswith("ghs_") or token.startswith("github_pat_") or token.startswith("ghp_")) else f"Bearer {token}"
    return {
        "Authorization": auth_header,
        "Accept": "application/vnd.github+json",
        "User-Agent": "CodeSage-AI-Agent"
    }


# ======================================================
# PR FILES
# ======================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying GitHub API request (attempt {retry_state.attempt_number})..."
    ),
)
def _fetch_pr_files_page(owner: str, repo: str, pr_number: int, page: int, per_page: int = 100) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    params = {"page": page, "per_page": per_page}

    def _make_req():
        resp = requests.get(
            url,
            headers=_get_headers(),
            params=params,
            timeout=settings.GITHUB_API_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    return github_api_circuit_breaker.call(_make_req)


def get_pr_files(owner: str, repo: str, pr_number: int, max_pages: int = 10) -> List[Dict[str, str]]:
    """
    Fetches all changed files for a pull request using GitHub REST API pagination.
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
                break

            page += 1

        logger.info(f"Successfully retrieved {len(all_files)} total file entry/entries for PR #{pr_number}.")
        return all_files

    except Exception as e:
        logger.error(f"Failed to fetch PR files for {owner}/{repo}#{pr_number}: {e}")
        return []


# ======================================================
# REPOSITORY METADATA READ API
# ======================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning("Retrying GitHub get_repository request..."),
    reraise=True
)
def get_repository(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Fetches repository metadata from GitHub REST API (GET /repos/{owner}/{repo}).
    Returns None if repository does not exist (404) or on error.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        response = requests.get(url, headers=_get_headers(), timeout=settings.GITHUB_API_TIMEOUT)
        if response.status_code == 404:
            logger.warning(f"Repository {owner}/{repo} not found on GitHub (404).")
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch repository metadata for {owner}/{repo}: {e}")
        return None


# ======================================================
# PULL REQUEST READ APIs
# ======================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning("Retrying GitHub list_pull_requests page..."),
    reraise=True
)
def _fetch_pull_requests_page(owner: str, repo: str, state: str, page: int, per_page: int = 100) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    params = {"state": state, "page": page, "per_page": per_page}
    response = requests.get(url, headers=_get_headers(), params=params, timeout=settings.GITHUB_API_TIMEOUT)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json()


def list_pull_requests(owner: str, repo: str, state: str = "all", max_pages: int = 5) -> List[Dict[str, Any]]:
    """
    Lists pull requests for a repository using GitHub REST API pagination.
    """
    all_prs: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    try:
        while page <= max_pages:
            prs_page = _fetch_pull_requests_page(owner, repo, state=state, page=page, per_page=per_page)
            if not prs_page:
                break
            all_prs.extend(prs_page)
            if len(prs_page) < per_page:
                break
            page += 1

        return all_prs
    except Exception as e:
        logger.error(f"Failed to list pull requests for {owner}/{repo}: {e}")
        return []


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning("Retrying GitHub get_pull_request..."),
    reraise=True
)
def get_pull_request(owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
    """
    Fetches detailed metadata for a single pull request (GET /repos/{owner}/{repo}/pulls/{pr_number}).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        response = requests.get(url, headers=_get_headers(), timeout=settings.GITHUB_API_TIMEOUT)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch pull request {owner}/{repo}#{pr_number}: {e}")
        return None


# ======================================================
# ISSUE COMMENTS READ API
# ======================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning("Retrying GitHub list_issue_comments page..."),
    reraise=True
)
def _fetch_issue_comments_page(owner: str, repo: str, issue_number: int, page: int, per_page: int = 100) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    params = {"page": page, "per_page": per_page}
    response = requests.get(url, headers=_get_headers(), params=params, timeout=settings.GITHUB_API_TIMEOUT)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return response.json()


def list_issue_comments(owner: str, repo: str, issue_number: int, max_pages: int = 5) -> List[Dict[str, Any]]:
    """
    Lists comments for an issue / pull request using GitHub REST API pagination.
    """
    all_comments: List[Dict[str, Any]] = []
    page = 1
    per_page = 100

    try:
        while page <= max_pages:
            comments_page = _fetch_issue_comments_page(owner, repo, issue_number, page=page, per_page=per_page)
            if not comments_page:
                break
            all_comments.extend(comments_page)
            if len(comments_page) < per_page:
                break
            page += 1

        return all_comments
    except Exception as e:
        logger.error(f"Failed to list issue comments for {owner}/{repo}#{issue_number}: {e}")
        return []


# ======================================================
# COMMENT ON PR (POST)
# ======================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning("Retrying GitHub comment_on_pr..."),
    reraise=True
)
def comment_on_pr(repo_full_name: str, pr_number: int, comment: str) -> int:
    """
    Posts a review comment to a GitHub Pull Request thread.
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=6),
    retry=retry_if_exception(_is_transient_github_error),
    before_sleep=lambda retry_state: logger.warning("Retrying GitHub post_pull_request_review..."),
    reraise=True
)
def post_pull_request_review(
    repo_full_name: str,
    pr_number: int,
    body: str,
    event: str = "COMMENT",
    comments: Optional[List[Dict[str, Any]]] = None
) -> int:
    """
    Posts an official GitHub Pull Request Review (POST /repos/{owner}/{repo}/pulls/{pr_number}/reviews)
    supporting optional inline review comments attached to changed lines.
    Falls back to simple issue comment if pull request review fails.
    """
    url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}/reviews"
    payload: Dict[str, Any] = {
        "body": body,
        "event": event if event in ("APPROVE", "REQUEST_CHANGES", "COMMENT") else "COMMENT"
    }
    if comments:
        payload["comments"] = comments

    try:
        response = requests.post(
            url,
            headers=_get_headers(),
            json=payload,
            timeout=settings.GITHUB_API_TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"Successfully posted PR review to {repo_full_name}#{pr_number} (HTTP {response.status_code}).")
        return response.status_code
    except Exception as e:
        logger.warning(f"Failed posting official PR review to {repo_full_name}#{pr_number}: {e}. Falling back to issue comment...")
        return comment_on_pr(repo_full_name, pr_number, body)
import time
import logging
from typing import Optional, Dict, Any
import requests
import jwt
from app.config import settings

logger = logging.getLogger("codesage.github_app")

_TOKEN_CACHE: Dict[int, Dict[str, Any]] = {}


def generate_app_jwt() -> Optional[str]:
    """
    Generates a RS256 signed JWT for GitHub App authentication (valid for 10 minutes).
    Returns None if GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY are unconfigured.
    """
    app_id = settings.GITHUB_APP_ID
    private_key = settings.GITHUB_APP_PRIVATE_KEY

    if not app_id or not private_key:
        logger.debug("GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY not set. Using token fallback mode.")
        return None

    try:
        now = int(time.time())
        payload = {
            "iat": now - 60,  # 60s buffer for clock skew
            "exp": now + (10 * 60),  # Max 10 minutes validity
            "iss": str(app_id)
        }
        encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to generate GitHub App JWT: {e}")
        return None


def get_installation_access_token(installation_id: int) -> Optional[str]:
    """
    Retrieves or refreshes an installation access token for a specific GitHub App installation.
    Falls back to settings.GITHUB_TOKEN if GitHub App credentials are not configured.
    """
    app_jwt = generate_app_jwt()
    if not app_jwt:
        return settings.GITHUB_TOKEN

    # Check cache first
    now = time.time()
    cached = _TOKEN_CACHE.get(installation_id)
    if cached and cached["expires_at"] > now + 60:
        return cached["token"]

    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        response = requests.post(url, headers=headers, timeout=settings.GITHUB_API_TIMEOUT)
        if response.status_code == 201:
            data = response.json()
            token = data.get("token")
            # Parse expires_at if provided or default to 50 minutes
            _TOKEN_CACHE[installation_id] = {
                "token": token,
                "expires_at": now + (50 * 60)
            }
            logger.info(f"Generated new installation token for installation #{installation_id}")
            return token
        else:
            logger.error(f"GitHub App access token error ({response.status_code}): {response.text}")
            return settings.GITHUB_TOKEN
    except Exception as e:
        logger.error(f"Exception fetching installation token for #{installation_id}: {e}")
        return settings.GITHUB_TOKEN


def list_app_installations_from_github() -> list:
    """
    Fetches all active installations for the GitHub App via GitHub App JWT API.
    Returns list of raw installation dictionary objects from GitHub REST API.
    """
    app_jwt = generate_app_jwt()
    if not app_jwt:
        return []

    url = "https://api.github.com/app/installations"
    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        response = requests.get(url, headers=headers, timeout=settings.GITHUB_API_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to list GitHub App installations ({response.status_code}): {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception listing GitHub App installations: {e}")
        return []


def sync_installations_and_repositories(db: Any) -> list:
    """
    Reconciles and synchronizes GitHub App installations and monitored repositories into DB.
    1. Attempts live GitHub App JWT query (`GET /app/installations`).
    2. Fallback: If App JWT is not set or returns empty, checks known installation ID (110240187)
       or configured monitored repositories (`Tejas190605/ResumeIQ`) and registers installation + repo links.
    """
    from app.db_repositories.installation_repo import (
        upsert_installation,
        list_installations,
        link_repository_installation,
    )
    from app.db_repositories.repository_repo import upsert_repository

    gh_installations = list_app_installations_from_github()
    if gh_installations:
        for inst_data in gh_installations:
            inst_id = inst_data.get("id")
            account = inst_data.get("account", {}) or {}
            account_login = account.get("login", "Tejas190605")
            account_id = account.get("id", 0)
            account_type = account.get("type", "User")
            target_type = inst_data.get("target_type", "User")
            repo_selection = inst_data.get("repository_selection", "all")

            if inst_id:
                inst_model = upsert_installation(
                    db=db,
                    installation_id=inst_id,
                    account_login=account_login,
                    account_id=account_id,
                    account_type=account_type,
                    target_type=target_type,
                    repository_selection=repo_selection,
                    status="active"
                )
                for owner, repo in settings.monitored_repositories:
                    if owner.lower() == account_login.lower():
                        full_name = f"{owner}/{repo}"
                        upsert_repository(db, owner=owner, name=repo)
                        link_repository_installation(db, full_name, inst_model.id)

    existing = list_installations(db)
    if not existing:
        # Reconcile known installation 110240187 for Tejas190605 / ResumeIQ
        inst_model = upsert_installation(
            db=db,
            installation_id=110240187,
            account_login="Tejas190605",
            account_id=0,
            account_type="User",
            target_type="User",
            repository_selection="selected",
            status="active"
        )
        for owner, repo in settings.monitored_repositories:
            full_name = f"{owner}/{repo}"
            db_repo = upsert_repository(db, owner=owner, name=repo)
            link_repository_installation(db, full_name, inst_model.id)

    return list_installations(db)

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

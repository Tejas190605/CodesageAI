import logging
import urllib.parse
from typing import Dict, Any, List
import requests
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.security.jwt_auth import create_access_token, get_current_user
from app.db_repositories.user_repo import (
    upsert_user,
    upsert_organization,
    add_user_org_membership,
    get_user_organizations,
)
from app.models.db import User

logger = logging.getLogger("codesage.routes.auth")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/github/login")
def github_login(request: Request):
    """Returns or redirects to GitHub OAuth 2.0 authorization URL."""
    client_id = settings.GITHUB_CLIENT_ID
    if not client_id:
        # Development fallback mode URL
        return {
            "oauth_enabled": False,
            "message": "GITHUB_CLIENT_ID is not configured in .env. Running in local development auth fallback mode.",
            "auth_url": None
        }

    callback_url = str(request.url_for("github_callback"))
    if callback_url.startswith("http://") and "localhost" not in callback_url and "127.0.0.1" not in callback_url:
        callback_url = "https://" + callback_url[7:]

    params = {
        "client_id": client_id,
        "scope": "read:user user:email read:org",
        "redirect_uri": callback_url
    }
    url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    return {"oauth_enabled": True, "auth_url": url}


@router.get("/github/callback")
def github_callback(code: str, response: Response, db: Session = Depends(get_db)):
    """
    GitHub OAuth callback endpoint. Exchanges code for GitHub user access token,
    fetches GitHub profile & orgs, creates/updates User in DB, and sets HTTP-only session cookie.
    """
    client_id = settings.GITHUB_CLIENT_ID
    client_secret = settings.GITHUB_CLIENT_SECRET

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET is unconfigured."
        )

    # 1. Exchange code for GitHub access token
    token_url = "https://github.com/login/oauth/access_token"
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code
    }
    headers = {"Accept": "application/json"}

    try:
        token_res = requests.post(token_url, json=token_payload, headers=headers, timeout=settings.GITHUB_API_TIMEOUT)
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for GitHub token")
        token_data = token_res.json()
        gh_access_token = token_data.get("access_token")
        if not gh_access_token:
            raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {token_data.get('error_description')}")
    except Exception as e:
        logger.error(f"GitHub OAuth token exchange exception: {e}")
        raise HTTPException(status_code=500, detail="OAuth provider error")

    # 2. Fetch user profile from GitHub API
    gh_headers = {"Authorization": f"Bearer {gh_access_token}", "Accept": "application/vnd.github+json"}
    user_res = requests.get("https://api.github.com/user", headers=gh_headers, timeout=settings.GITHUB_API_TIMEOUT)
    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch GitHub user profile")
    user_data = user_res.json()

    github_id = user_data.get("id")
    username = user_data.get("login")
    email = user_data.get("email")
    name = user_data.get("name")
    avatar_url = user_data.get("avatar_url")

    # Upsert user record in DB
    user = upsert_user(
        db=db,
        github_id=github_id,
        username=username,
        email=email,
        name=name,
        avatar_url=avatar_url,
        role="admin" if username == "Tejas190605" else "member"
    )

    # 3. Fetch user organizations from GitHub API
    try:
        orgs_res = requests.get("https://api.github.com/user/orgs", headers=gh_headers, timeout=settings.GITHUB_API_TIMEOUT)
        if orgs_res.status_code == 200:
            orgs_data = orgs_res.json()
            for org_info in orgs_data:
                org = upsert_organization(
                    db=db,
                    github_id=org_info.get("id"),
                    login=org_info.get("login"),
                    avatar_url=org_info.get("avatar_url"),
                    description=org_info.get("description")
                )
                add_user_org_membership(db=db, user_id=user.id, org_id=org.id, role="member")
    except Exception as e:
        logger.warning(f"Error fetching user organizations: {e}")

    # 4. Generate application JWT access token
    access_token = create_access_token({"sub": str(user.id), "username": user.username, "role": user.role})

    # Record Audit Event safely
    from app.services.audit_service import record_event
    record_event(
        db=db,
        event_type="user.login",
        actor=user.username,
        user_id=user.id,
        description=f"User '{user.username}' logged in via GitHub OAuth."
    )

    # Set HTTP-only cookie for secure session persistence
    redirect_target = f"{settings.FRONTEND_URL.rstrip('/')}/profile"
    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        key="codesage_session",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns current authenticated user profile, assigned role, and organizations."""
    orgs = get_user_organizations(db, current_user.id)
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role,
        "organizations": [
            {
                "id": o.id,
                "github_id": o.github_id,
                "login": o.login,
                "avatar_url": o.avatar_url
            }
            for o in orgs
        ]
    }


@router.post("/logout")
def logout(response: Response):
    """Clears HTTP-only session cookies and logs user out."""
    response.delete_cookie("codesage_session")
    return {"status": "logged_out", "message": "Successfully logged out."}

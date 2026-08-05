import pytest
from sqlalchemy.orm import Session
from app.models.db import User, Organization, OrgMembership, Installation, Repository
from app.db_repositories.user_repo import (
    upsert_user,
    get_user_by_id,
    get_user_by_github_id,
    upsert_organization,
    add_user_org_membership,
    get_user_organizations,
)
from app.db_repositories.installation_repo import (
    upsert_installation,
    get_installation_by_id,
    list_installations,
    link_repository_installation,
)
from app.services.github_app_service import generate_app_jwt, get_installation_access_token
from app.security.jwt_auth import create_access_token, decode_access_token
from tests.test_webhooks import _sign_payload
import json


def test_user_and_org_repository_crud(db_session: Session):
    """Tests CRUD operations for User, Organization, and OrgMembership DB repositories."""
    user = upsert_user(
        db=db_session,
        github_id=12345,
        username="octocat",
        email="octocat@github.com",
        name="The Octocat",
        role="admin"
    )
    assert user.id is not None
    assert user.username == "octocat"
    assert user.role == "admin"

    fetched_user = get_user_by_github_id(db_session, 12345)
    assert fetched_user is not None
    assert fetched_user.username == "octocat"

    org = upsert_organization(
        db=db_session,
        github_id=999,
        login="acme-corp",
        description="ACME Engineering"
    )
    assert org.id is not None
    assert org.login == "acme-corp"

    membership = add_user_org_membership(db_session, user.id, org.id, role="admin")
    assert membership.role == "admin"

    user_orgs = get_user_organizations(db_session, user.id)
    assert len(user_orgs) == 1
    assert user_orgs[0].login == "acme-corp"


def test_installation_repository_crud(db_session: Session):
    """Tests CRUD operations for GitHub App Installation database models."""
    inst = upsert_installation(
        db=db_session,
        installation_id=554433,
        account_login="Tejas190605",
        account_id=1001,
        account_type="User",
        status="active"
    )
    assert inst.id is not None
    assert inst.installation_id == 554433

    fetched = get_installation_by_id(db_session, 554433)
    assert fetched is not None
    assert fetched.account_login == "Tejas190605"

    all_insts = list_installations(db_session)
    assert len(all_insts) == 1

    # Link to repository
    repo = Repository(owner="Tejas190605", name="codexproj", full_name="Tejas190605/codexproj")
    db_session.add(repo)
    db_session.commit()

    linked = link_repository_installation(db_session, "Tejas190605/codexproj", inst.id)
    assert linked is True


def test_jwt_access_token_creation_and_decoding():
    """Tests signing and decoding application JWT access tokens."""
    token = create_access_token({"sub": "42", "username": "testuser", "role": "admin"})
    assert token is not None

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["username"] == "testuser"
    assert payload["role"] == "admin"


def test_github_app_jwt_fallback_mode():
    """Tests GitHub App JWT generation fallback when credentials are default/empty."""
    app_jwt = generate_app_jwt()
    assert app_jwt is None

    token = get_installation_access_token(1234)
    assert token is not None  # Fallback to GITHUB_TOKEN


def test_auth_me_and_logout_endpoints(client):
    """Tests /api/auth/me and /api/auth/logout HTTP endpoints."""
    res_me = client.get("/api/auth/me")
    assert res_me.status_code == 200
    data_me = res_me.json()
    assert "username" in data_me
    assert "role" in data_me

    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200
    assert res_logout.json()["status"] == "logged_out"


def test_installations_and_onboard_endpoints(client):
    """Tests GET /api/installations and POST /api/installations/onboard endpoints."""
    res_list = client.get("/api/installations")
    assert res_list.status_code == 200

    onboard_payload = {
        "owner": "testowner",
        "name": "newrepo",
        "default_branch": "main",
        "private": False
    }
    res_onboard = client.post("/api/installations/onboard", json=onboard_payload)
    assert res_onboard.status_code == 200
    assert res_onboard.json()["status"] == "onboarded"
    assert res_onboard.json()["repository"] == "testowner/newrepo"


def test_github_app_installation_webhooks(client, dummy_secret):
    """Tests handling of installation and installation_repositories GitHub webhook events."""
    payload = {
        "action": "created",
        "installation": {
            "id": 887766,
            "account": {"login": "testorg", "id": 500, "type": "Organization"},
            "target_type": "Organization",
            "repository_selection": "all"
        }
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    res = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "installation",
            "X-GitHub-Delivery": "deliv-inst-001",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert res.status_code == 200
    assert res.json()["status"] == "received"
    assert res.json()["event"] == "installation"

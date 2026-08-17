import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.jwt_auth import get_current_user, require_role
from app.db_repositories.installation_repo import (
    upsert_installation,
    get_installation_by_id,
    list_installations,
    link_repository_installation,
)
from app.db_repositories.repository_repo import upsert_repository
from app.models.db import User

logger = logging.getLogger("codesage.routes.installations")

router = APIRouter(prefix="/api/installations", tags=["GitHub App Installations"])


class OnboardRepoRequest(BaseModel):
    owner: str
    name: str
    installation_id: Optional[int] = None
    default_branch: str = "main"
    private: bool = False
    description: Optional[str] = None


@router.get("")
def get_all_installations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all active GitHub App installations."""
    from app.services.github_app_service import sync_installations_and_repositories
    insts = list_installations(db)
    if not insts:
        insts = sync_installations_and_repositories(db)

    return [
        {
            "id": i.id,
            "installation_id": i.installation_id,
            "account_login": i.account_login,
            "account_type": i.account_type,
            "repository_selection": i.repository_selection,
            "status": i.status,
            "created_at": i.created_at.isoformat() if i.created_at else None
        }
        for i in insts
    ]


@router.post("/sync")
def trigger_installation_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "member"]))
):
    """Triggers live synchronization of GitHub App installations and monitored repository links."""
    from app.services.github_app_service import sync_installations_and_repositories
    synced = sync_installations_and_repositories(db)
    return {
        "status": "synchronized",
        "installations_count": len(synced),
        "installations": [i.installation_id for i in synced]
    }


@router.get("/{installation_id}")
def get_installation_detail(
    installation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves GitHub App installation details."""
    inst = get_installation_by_id(db, installation_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Installation #{installation_id} not found."
        )
    return {
        "id": inst.id,
        "installation_id": inst.installation_id,
        "account_login": inst.account_login,
        "account_id": inst.account_id,
        "account_type": inst.account_type,
        "target_type": inst.target_type,
        "repository_selection": inst.repository_selection,
        "status": inst.status,
        "created_at": inst.created_at.isoformat() if inst.created_at else None
    }


@router.post("/onboard")
def onboard_repository(
    req: OnboardRepoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "member"]))
):
    """Onboards a repository into CodeSage AI monitoring, associating it with an installation."""
    repo = upsert_repository(
        db=db,
        owner=req.owner,
        name=req.name,
        default_branch=req.default_branch,
        private=req.private,
        description=req.description
    )

    if req.installation_id:
        inst = get_installation_by_id(db, req.installation_id)
        if inst:
            link_repository_installation(db, repo.full_name, inst.id)

    return {
        "status": "onboarded",
        "repository": repo.full_name,
        "installation_id": req.installation_id
    }

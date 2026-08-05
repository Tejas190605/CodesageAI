import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.db import Installation, Repository

logger = logging.getLogger("codesage.db_repositories.installation")


def upsert_installation(
    db: Session,
    installation_id: int,
    account_login: str,
    account_id: int,
    account_type: str = "User",
    target_type: str = "User",
    repository_selection: str = "all",
    status: str = "active"
) -> Installation:
    """Creates or updates a GitHub App Installation record."""
    inst = db.query(Installation).filter(Installation.installation_id == installation_id).first()
    if inst:
        inst.account_login = account_login
        inst.account_id = account_id
        inst.account_type = account_type
        inst.target_type = target_type
        inst.repository_selection = repository_selection
        inst.status = status
    else:
        inst = Installation(
            installation_id=installation_id,
            account_login=account_login,
            account_id=account_id,
            account_type=account_type,
            target_type=target_type,
            repository_selection=repository_selection,
            status=status
        )
        db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def get_installation_by_id(db: Session, installation_id: int) -> Optional[Installation]:
    """Retrieves an installation by GitHub installation_id."""
    return db.query(Installation).filter(Installation.installation_id == installation_id).first()


def get_installation_by_account(db: Session, account_login: str) -> Optional[Installation]:
    """Retrieves an installation by account login username/org."""
    return db.query(Installation).filter(
        Installation.account_login == account_login,
        Installation.status == "active"
    ).first()


def list_installations(db: Session) -> List[Installation]:
    """Lists all active GitHub App installations."""
    return db.query(Installation).filter(Installation.status == "active").all()


def link_repository_installation(db: Session, full_name: str, installation_db_id: int) -> bool:
    """Links a repository to a GitHub App installation."""
    repo = db.query(Repository).filter(Repository.full_name == full_name).first()
    if repo:
        repo.installation_id = installation_db_id
        db.commit()
        return True
    return False

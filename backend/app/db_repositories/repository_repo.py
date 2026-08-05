from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db import Repository


def get_repository_by_full_name(db: Session, full_name: str) -> Optional[Repository]:
    """Fetches a repository by full_name ('owner/repo') case-insensitively."""
    return db.query(Repository).filter(
        Repository.full_name.ilike(full_name.strip())
    ).first()


def get_repository_by_owner_repo(db: Session, owner: str, name: str) -> Optional[Repository]:
    """Fetches a repository by owner and repo name."""
    full_name = f"{owner.strip()}/{name.strip()}"
    return get_repository_by_full_name(db, full_name)


def upsert_repository(
    db: Session,
    owner: str,
    name: str,
    default_branch: str = "main",
    private: bool = False,
    description: Optional[str] = None
) -> Repository:
    """Creates a new repository or updates existing metadata."""
    owner_clean = owner.strip()
    name_clean = name.strip()
    full_name = f"{owner_clean}/{name_clean}"

    repo = get_repository_by_full_name(db, full_name)
    if repo:
        repo.owner = owner_clean
        repo.name = name_clean
        repo.default_branch = default_branch or repo.default_branch
        repo.private = private
        if description is not None:
            repo.description = description
    else:
        repo = Repository(
            owner=owner_clean,
            name=name_clean,
            full_name=full_name,
            default_branch=default_branch or "main",
            private=private,
            description=description
        )
        db.add(repo)

    db.commit()
    db.refresh(repo)
    return repo


def list_all_repositories(db: Session) -> List[Repository]:
    """Lists all monitored repositories recorded in database."""
    return db.query(Repository).order_by(Repository.full_name).all()

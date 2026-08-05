import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.db import User, Organization, OrgMembership

logger = logging.getLogger("codesage.db_repositories.user")


def upsert_user(
    db: Session,
    github_id: int,
    username: str,
    email: Optional[str] = None,
    name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    role: str = "member"
) -> User:
    """Creates or updates a User record in the database."""
    user = db.query(User).filter(User.github_id == github_id).first()
    if user:
        user.username = username
        if email:
            user.email = email
        if name:
            user.name = name
        if avatar_url:
            user.avatar_url = avatar_url
    else:
        user = User(
            github_id=github_id,
            username=username,
            email=email,
            name=name or username,
            avatar_url=avatar_url,
            role=role
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieves a user by database ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_github_id(db: Session, github_id: int) -> Optional[User]:
    """Retrieves a user by GitHub ID."""
    return db.query(User).filter(User.github_id == github_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieves a user by GitHub username."""
    return db.query(User).filter(User.username == username).first()


def upsert_organization(
    db: Session,
    github_id: int,
    login: str,
    avatar_url: Optional[str] = None,
    description: Optional[str] = None
) -> Organization:
    """Creates or updates an Organization record."""
    org = db.query(Organization).filter(Organization.github_id == github_id).first()
    if org:
        org.login = login
        if avatar_url:
            org.avatar_url = avatar_url
        if description:
            org.description = description
    else:
        org = Organization(
            github_id=github_id,
            login=login,
            avatar_url=avatar_url,
            description=description
        )
        db.add(org)
    db.commit()
    db.refresh(org)
    return org


def add_user_org_membership(
    db: Session,
    user_id: int,
    org_id: int,
    role: str = "member"
) -> OrgMembership:
    """Links a user to an organization with a specific role."""
    membership = db.query(OrgMembership).filter(
        OrgMembership.user_id == user_id,
        OrgMembership.org_id == org_id
    ).first()
    if membership:
        membership.role = role
    else:
        membership = OrgMembership(user_id=user_id, org_id=org_id, role=role)
        db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def get_user_organizations(db: Session, user_id: int) -> List[Organization]:
    """Retrieves all organizations that a user is a member of."""
    memberships = db.query(OrgMembership).filter(OrgMembership.user_id == user_id).all()
    org_ids = [m.org_id for m in memberships]
    if not org_ids:
        return []
    return db.query(Organization).filter(Organization.id.in_(org_ids)).all()

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db import PullRequest


def get_pull_request_by_number(
    db: Session,
    repository_id: int,
    number: int
) -> Optional[PullRequest]:
    """Fetches a Pull Request by repository ID and PR number."""
    return db.query(PullRequest).filter(
        PullRequest.repository_id == repository_id,
        PullRequest.number == number
    ).first()


def upsert_pull_request(
    db: Session,
    repository_id: int,
    number: int,
    title: str,
    state: str = "open",
    author: Optional[str] = None,
    html_url: Optional[str] = None,
    additions: int = 0,
    deletions: int = 0,
    changed_files: int = 0,
    commits: int = 0,
    github_pr_id: Optional[int] = None
) -> PullRequest:
    """Creates or updates a Pull Request record in the database."""
    pr = get_pull_request_by_number(db, repository_id, number)
    if pr:
        pr.title = title
        pr.state = state
        if author:
            pr.author = author
        if html_url:
            pr.html_url = html_url
        if additions > 0:
            pr.additions = additions
        if deletions > 0:
            pr.deletions = deletions
        if changed_files > 0:
            pr.changed_files = changed_files
        if commits > 0:
            pr.commits = commits
        if github_pr_id:
            pr.github_pr_id = github_pr_id
    else:
        pr = PullRequest(
            repository_id=repository_id,
            number=number,
            title=title,
            state=state,
            author=author,
            html_url=html_url,
            additions=additions,
            deletions=deletions,
            changed_files=changed_files,
            commits=commits,
            github_pr_id=github_pr_id
        )
        db.add(pr)

    db.commit()
    db.refresh(pr)
    return pr


def list_pull_requests_for_repo(
    db: Session,
    repository_id: int,
    state: Optional[str] = None
) -> List[PullRequest]:
    """Lists Pull Requests for a repository filtered optionally by state ('open', 'closed', 'all')."""
    query = db.query(PullRequest).filter(PullRequest.repository_id == repository_id)
    if state and state.lower() != "all":
        query = query.filter(PullRequest.state == state.lower())
    return query.order_by(PullRequest.number.desc()).all()

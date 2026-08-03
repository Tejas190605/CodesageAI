import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.config import settings
from app.models.github import (
    RepositorySummary,
    PullRequestSummary,
    PullRequestDetail,
    ReviewCommentSummary,
    PullRequestReviewResponse,
    DashboardSummary,
)
from app.services.github_service import (
    get_repository,
    list_pull_requests,
    get_pull_request,
    list_issue_comments,
)
from app.services.review_renderer import (
    is_codesage_review_comment,
    extract_overall_rating_from_markdown,
)

logger = logging.getLogger("codesage.routes.api")

router = APIRouter(prefix="/api", tags=["dashboard-api"])


def _is_repo_configured(owner: str, repo: str) -> bool:
    """Verifies whether an (owner, repo) pair is configured in CODESAGE_REPOSITORIES."""
    configured = settings.monitored_repositories
    target = (owner.lower(), repo.lower())
    return any(c_owner.lower() == target[0] and c_repo.lower() == target[1] for c_owner, c_repo in configured)


def _map_github_pr_summary(pr_data: dict) -> PullRequestSummary:
    """Helper converting GitHub PR JSON dict into a PullRequestSummary object."""
    user = pr_data.get("user", {}) or {}
    head = pr_data.get("head", {}) or {}
    base = pr_data.get("base", {}) or {}
    return PullRequestSummary(
        number=pr_data.get("number", 0),
        title=pr_data.get("title", ""),
        state=pr_data.get("state", "open"),
        draft=pr_data.get("draft", False),
        author=user.get("login", "unknown"),
        html_url=pr_data.get("html_url", ""),
        created_at=pr_data.get("created_at"),
        updated_at=pr_data.get("updated_at"),
        head_branch=head.get("ref", ""),
        base_branch=base.get("ref", "")
    )


# ======================================================
# DASHBOARD ENDPOINT
# ======================================================

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary() -> DashboardSummary:
    """
    Aggregates code health metrics and recent PR reviews across monitored repositories.
    """
    monitored = settings.monitored_repositories
    if not monitored:
        return DashboardSummary(
            repositories_count=0,
            open_pull_requests=0,
            reviewed_pull_requests=0,
            recent_pull_requests=[],
            average_score=None
        )

    open_prs_count = 0
    reviewed_prs_count = 0
    recent_prs: List[PullRequestSummary] = []
    scores: List[int] = []

    for owner, repo in monitored:
        # Fetch open PRs
        open_prs_data = list_pull_requests(owner, repo, state="open", max_pages=2)
        open_prs_count += len(open_prs_data)

        # Collect recent PR summaries
        for pr_raw in open_prs_data[:5]:
            recent_prs.append(_map_github_pr_summary(pr_raw))

            # Inspect comments for review status and score
            pr_num = pr_raw.get("number")
            if pr_num:
                comments = list_issue_comments(owner, repo, pr_num, max_pages=1)
                codesage_comments = [c for c in comments if is_codesage_review_comment(c.get("body", ""))]
                if codesage_comments:
                    reviewed_prs_count += 1
                    latest_comment = codesage_comments[-1]
                    score = extract_overall_rating_from_markdown(latest_comment.get("body", ""))
                    if score is not None:
                        scores.append(score)

    avg_score = round(sum(scores) / len(scores), 1) if scores else None

    return DashboardSummary(
        repositories_count=len(monitored),
        open_pull_requests=open_prs_count,
        reviewed_pull_requests=reviewed_prs_count,
        recent_pull_requests=recent_prs[:10],
        average_score=avg_score
    )


# ======================================================
# REPOSITORIES ENDPOINTS
# ======================================================

@router.get("/repositories", response_model=List[RepositorySummary])
def list_monitored_repositories() -> List[RepositorySummary]:
    """
    Returns configured monitored repositories with live GitHub metadata.
    """
    monitored = settings.monitored_repositories
    results: List[RepositorySummary] = []

    for owner, repo in monitored:
        repo_data = get_repository(owner, repo)
        if not repo_data:
            logger.warning(f"Could not fetch repository metadata for monitored repo {owner}/{repo}.")
            continue

        open_prs = list_pull_requests(owner, repo, state="open", max_pages=1)

        results.append(
            RepositorySummary(
                owner=owner,
                name=repo,
                full_name=repo_data.get("full_name", f"{owner}/{repo}"),
                description=repo_data.get("description"),
                private=repo_data.get("private", False),
                default_branch=repo_data.get("default_branch", "main"),
                html_url=repo_data.get("html_url", f"https://github.com/{owner}/{repo}"),
                open_pull_requests=len(open_prs),
                updated_at=repo_data.get("updated_at")
            )
        )

    return results


@router.get("/repositories/{owner}/{repo}")
def get_repository_detail(owner: str, repo: str):
    """
    Returns repository metadata and open pull request list for a configured repo.
    """
    if not _is_repo_configured(owner, repo):
        raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' is not configured in CodeSage.")

    repo_data = get_repository(owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' not found on GitHub.")

    prs_data = list_pull_requests(owner, repo, state="all", max_pages=2)
    prs_summaries = [_map_github_pr_summary(pr) for pr in prs_data]

    return {
        "repository": RepositorySummary(
            owner=owner,
            name=repo,
            full_name=repo_data.get("full_name", f"{owner}/{repo}"),
            description=repo_data.get("description"),
            private=repo_data.get("private", False),
            default_branch=repo_data.get("default_branch", "main"),
            html_url=repo_data.get("html_url", f"https://github.com/{owner}/{repo}"),
            open_pull_requests=sum(1 for p in prs_summaries if p.state == "open"),
            updated_at=repo_data.get("updated_at")
        ),
        "pull_requests": prs_summaries
    }


@router.get("/repositories/{owner}/{repo}/pulls", response_model=List[PullRequestSummary])
def get_repository_pulls(
    owner: str,
    repo: str,
    state: str = Query("all", pattern="^(open|closed|all)$")
) -> List[PullRequestSummary]:
    """
    Lists pull requests for a configured repository filtered by state ('open', 'closed', 'all').
    """
    if not _is_repo_configured(owner, repo):
        raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' is not configured in CodeSage.")

    prs_data = list_pull_requests(owner, repo, state=state, max_pages=5)
    return [_map_github_pr_summary(pr) for pr in prs_data]


# ======================================================
# PULL REQUEST & REVIEW DETAIL ENDPOINTS
# ======================================================

@router.get("/pulls/{owner}/{repo}/{number}", response_model=PullRequestDetail)
def get_pull_request_detail(owner: str, repo: str, number: int) -> PullRequestDetail:
    """
    Fetches detailed GitHub metadata for a pull request.
    """
    if not _is_repo_configured(owner, repo):
        raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' is not configured in CodeSage.")

    pr_data = get_pull_request(owner, repo, number)
    if not pr_data:
        raise HTTPException(status_code=404, detail=f"Pull request #{number} not found for '{owner}/{repo}'.")

    summary = _map_github_pr_summary(pr_data)
    return PullRequestDetail(
        **summary.model_dump(),
        changed_files=pr_data.get("changed_files", 0),
        additions=pr_data.get("additions", 0),
        deletions=pr_data.get("deletions", 0),
        commits=pr_data.get("commits", 0),
        comments=pr_data.get("comments", 0)
    )


@router.get("/pulls/{owner}/{repo}/{number}/review", response_model=PullRequestReviewResponse)
def get_pull_request_review_status(owner: str, repo: str, number: int) -> PullRequestReviewResponse:
    """
    Fetches CodeSage review status and latest review details for a pull request.
    """
    if not _is_repo_configured(owner, repo):
        raise HTTPException(status_code=404, detail=f"Repository '{owner}/{repo}' is not configured in CodeSage.")

    comments = list_issue_comments(owner, repo, number, max_pages=5)
    codesage_comments = [c for c in comments if is_codesage_review_comment(c.get("body", ""))]

    if not codesage_comments:
        return PullRequestReviewResponse(
            repository=f"{owner}/{repo}",
            pull_number=number,
            reviewed=False,
            review_count=0,
            latest_review=None
        )

    # Sort comments chronologically
    codesage_comments.sort(key=lambda c: c.get("created_at", ""))
    latest = codesage_comments[-1]

    score = extract_overall_rating_from_markdown(latest.get("body", ""))

    latest_summary = ReviewCommentSummary(
        comment_id=latest.get("id", 0),
        created_at=latest.get("created_at", ""),
        updated_at=latest.get("updated_at", ""),
        overall_rating=score,
        markdown=latest.get("body", "")
    )

    return PullRequestReviewResponse(
        repository=f"{owner}/{repo}",
        pull_number=number,
        reviewed=True,
        review_count=len(codesage_comments),
        latest_review=latest_summary
    )

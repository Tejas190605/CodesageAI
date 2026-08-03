from typing import List, Optional
from pydantic import BaseModel, Field


class RepositorySummary(BaseModel):
    """Repository metadata summary for dashboard lists."""
    owner: str = Field(description="Repository owner or organization name")
    name: str = Field(description="Repository name")
    full_name: str = Field(description="Full repository identifier ('owner/repo')")
    description: Optional[str] = Field(default=None, description="Repository description")
    private: bool = Field(default=False, description="Is repository private")
    default_branch: str = Field(default="main", description="Default branch name")
    html_url: str = Field(description="GitHub repository HTML URL")
    open_pull_requests: int = Field(default=0, description="Count of open pull requests")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")


class PullRequestSummary(BaseModel):
    """Pull request summary object for list views."""
    number: int = Field(description="Pull request number")
    title: str = Field(description="Pull request title")
    state: str = Field(description="Pull request state ('open', 'closed')")
    draft: bool = Field(default=False, description="Is pull request a draft")
    author: str = Field(description="Author GitHub username")
    html_url: str = Field(description="GitHub pull request HTML URL")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    head_branch: str = Field(description="Head branch name")
    base_branch: str = Field(description="Base branch name")


class PullRequestDetail(PullRequestSummary):
    """Detailed pull request metadata with stats."""
    changed_files: int = Field(default=0, description="Count of changed files")
    additions: int = Field(default=0, description="Lines added")
    deletions: int = Field(default=0, description="Lines deleted")
    commits: int = Field(default=0, description="Commit count")
    comments: int = Field(default=0, description="Comment count")


class ReviewCommentSummary(BaseModel):
    """Summary of a CodeSage review comment posted to GitHub."""
    comment_id: int = Field(description="GitHub comment ID")
    created_at: str = Field(description="Comment creation timestamp")
    updated_at: str = Field(description="Comment last updated timestamp")
    overall_rating: Optional[int] = Field(default=None, description="Parsed score rating (1-10) if extractable")
    markdown: str = Field(description="Full rendered Markdown review text")


class PullRequestReviewResponse(BaseModel):
    """Response model for PR CodeSage review metadata and latest review content."""
    repository: str = Field(description="Full repository identifier ('owner/repo')")
    pull_number: int = Field(description="Pull request number")
    reviewed: bool = Field(description="True if CodeSage has posted at least one review")
    review_count: int = Field(default=0, description="Total count of CodeSage reviews posted")
    latest_review: Optional[ReviewCommentSummary] = Field(default=None, description="Latest CodeSage review details")


class DashboardSummary(BaseModel):
    """Aggregated dashboard statistics model."""
    repositories_count: int = Field(description="Count of monitored repositories")
    open_pull_requests: int = Field(description="Total open pull requests across monitored repos")
    reviewed_pull_requests: int = Field(description="Total PRs with CodeSage reviews")
    recent_pull_requests: List[PullRequestSummary] = Field(default_factory=list, description="Recent pull requests")
    average_score: Optional[float] = Field(default=None, description="Average quality score across extractable reviews")

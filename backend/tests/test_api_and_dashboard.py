import pytest
from unittest.mock import MagicMock
from app.config import Settings
from app.services.review_renderer import (
    is_codesage_review_comment,
    extract_overall_rating_from_markdown,
    CODESAGE_REVIEW_MARKER,
)
from app.services.github_service import (
    get_repository,
    list_pull_requests,
    get_pull_request,
    list_issue_comments,
)


def test_repo_config_parsing():
    """Tests parsing of CODESAGE_REPOSITORIES string into (owner, repo) tuples."""
    s = Settings(
        GEMINI_API_KEY="key",
        GITHUB_TOKEN="token",
        GITHUB_WEBHOOK_SECRET="secret",
        CODESAGE_REPOSITORIES="owner1/repo1, owner2/repo2 "
    )
    repos = s.monitored_repositories
    assert len(repos) == 2
    assert repos[0] == ("owner1", "repo1")
    assert repos[1] == ("owner2", "repo2")


def test_repo_config_empty():
    """Tests empty CODESAGE_REPOSITORIES string."""
    s = Settings(
        GEMINI_API_KEY="key",
        GITHUB_TOKEN="token",
        GITHUB_WEBHOOK_SECRET="secret",
        CODESAGE_REPOSITORIES=""
    )
    assert s.monitored_repositories == []


def test_repo_config_malformed_entries():
    """Tests filtering out invalid/malformed repository entries."""
    s = Settings(
        GEMINI_API_KEY="key",
        GITHUB_TOKEN="token",
        GITHUB_WEBHOOK_SECRET="secret",
        CODESAGE_REPOSITORIES="invalid, owner/repo, bad/path/extra, /emptyowner, emptyrepo/"
    )
    assert s.monitored_repositories == [("owner", "repo")]


def test_get_repository_success(mocker):
    """Tests get_repository REST API call returns repository metadata dict."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = {
        "full_name": "owner/repo",
        "description": "Test repo",
        "private": False,
        "default_branch": "main",
        "html_url": "https://github.com/owner/repo"
    }
    mock_get.return_value = mock_res

    data = get_repository("owner", "repo")
    assert data is not None
    assert data["full_name"] == "owner/repo"


def test_get_repository_github_failure_returns_none(mocker):
    """Tests 404 response from GitHub returns None for get_repository."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=404)
    mock_get.return_value = mock_res

    data = get_repository("owner", "repo")
    assert data is None


def test_list_pull_requests_single_page(mocker):
    """Tests list_pull_requests fetches single page."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = [{"number": 1, "title": "PR 1", "state": "open"}]
    mock_get.return_value = mock_res

    prs = list_pull_requests("owner", "repo", state="open")
    assert len(prs) == 1
    assert prs[0]["number"] == 1


def test_list_pull_requests_pagination(mocker):
    """Tests list_pull_requests pagination across pages."""
    mock_get = mocker.patch("requests.get")
    res1 = MagicMock(status_code=200)
    res1.json.return_value = [{"number": i} for i in range(100)]
    res2 = MagicMock(status_code=200)
    res2.json.return_value = [{"number": i} for i in range(100, 110)]
    mock_get.side_effect = [res1, res2]

    prs = list_pull_requests("owner", "repo", state="all")
    assert len(prs) == 110


def test_get_pull_request_detail(mocker):
    """Tests get_pull_request REST API call."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = {"number": 5, "title": "PR Title", "state": "open"}
    mock_get.return_value = mock_res

    pr = get_pull_request("owner", "repo", 5)
    assert pr is not None
    assert pr["number"] == 5


def test_list_issue_comments_pagination(mocker):
    """Tests list_issue_comments pagination."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = [{"id": 1, "body": "Comment 1"}]
    mock_get.return_value = mock_res

    comments = list_issue_comments("owner", "repo", 5)
    assert len(comments) == 1


def test_is_codesage_review_comment_detection():
    """Tests canonical CodeSage review marker detection in comment body."""
    valid_comment = f"{CODESAGE_REVIEW_MARKER}\n\n## Summary\nGood PR"
    human_comment = "Looks good to me! LGTM"

    assert is_codesage_review_comment(valid_comment) is True
    assert is_codesage_review_comment(human_comment) is False
    assert is_codesage_review_comment("") is False


def test_extract_overall_rating_from_markdown():
    """Tests exact score extraction from CodeSage markdown comment."""
    markdown = f"{CODESAGE_REVIEW_MARKER}\n\n## Summary\nOK\n\n## Overall Rating\n**8/10**\n"
    assert extract_overall_rating_from_markdown(markdown) == 8


def test_extract_overall_rating_malformed_returns_none():
    """Tests that malformed or absent score blocks return None."""
    markdown = f"{CODESAGE_REVIEW_MARKER}\n\nNo score block here."
    human_comment = "Score is 10/10!"

    assert extract_overall_rating_from_markdown(markdown) is None
    assert extract_overall_rating_from_markdown(human_comment) is None


def test_api_repositories_endpoint(client, mocker):
    """Tests GET /api/repositories returns list of configured repositories."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")

    mocker.patch("app.routes.api.get_repository", return_value={
        "full_name": "testowner/testrepo",
        "description": "Test repo",
        "private": False,
        "default_branch": "main",
        "html_url": "https://github.com/testowner/testrepo",
        "updated_at": "2026-08-01T00:00:00Z"
    })
    mocker.patch("app.routes.api.list_pull_requests", return_value=[{"number": 1}])

    response = client.get("/api/repositories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["full_name"] == "testowner/testrepo"
    assert data[0]["open_pull_requests"] == 1


def test_api_repository_detail_endpoint(client, mocker):
    """Tests GET /api/repositories/{owner}/{repo}."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")

    mocker.patch("app.routes.api.get_repository", return_value={
        "full_name": "testowner/testrepo",
        "html_url": "https://github.com/testowner/testrepo"
    })
    mocker.patch("app.routes.api.list_pull_requests", return_value=[
        {"number": 1, "title": "PR 1", "state": "open"}
    ])

    response = client.get("/api/repositories/testowner/testrepo")
    assert response.status_code == 200
    data = response.json()
    assert "repository" in data
    assert "pull_requests" in data
    assert len(data["pull_requests"]) == 1


def test_api_unconfigured_repository_404(client, mocker):
    """Tests that querying an unconfigured repository returns HTTP 404."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "configured/repo")

    response = client.get("/api/repositories/unconfigured/repo")
    assert response.status_code == 404
    assert "not configured" in response.json()["detail"]


def test_api_pulls_endpoint_with_state_filters(client, mocker):
    """Tests GET /api/repositories/{owner}/{repo}/pulls with state query parameters."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")
    mock_list = mocker.patch("app.routes.api.list_pull_requests", return_value=[
        {"number": 1, "title": "Open PR", "state": "open"}
    ])

    res_all = client.get("/api/repositories/testowner/testrepo/pulls?state=all")
    assert res_all.status_code == 200
    mock_list.assert_called_with("testowner", "testrepo", state="all", max_pages=5)

    res_open = client.get("/api/repositories/testowner/testrepo/pulls?state=open")
    assert res_open.status_code == 200
    mock_list.assert_called_with("testowner", "testrepo", state="open", max_pages=5)


def test_api_pulls_endpoint_invalid_state_validation(client, mocker):
    """Tests that an invalid state query parameter raises FastAPI 422 validation error."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")

    response = client.get("/api/repositories/testowner/testrepo/pulls?state=invalid_state")
    assert response.status_code == 422


def test_api_pull_detail_endpoint(client, mocker):
    """Tests GET /api/pulls/{owner}/{repo}/{number}."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")
    mocker.patch("app.routes.api.get_pull_request", return_value={
        "number": 10,
        "title": "PR Detail",
        "state": "open",
        "user": {"login": "dev"},
        "head": {"ref": "feature"},
        "base": {"ref": "main"},
        "html_url": "https://github.com/testowner/testrepo/pull/10",
        "changed_files": 3,
        "additions": 50,
        "deletions": 10,
        "commits": 2,
        "comments": 1
    })

    response = client.get("/api/pulls/testowner/testrepo/10")
    assert response.status_code == 200
    data = response.json()
    assert data["number"] == 10
    assert data["changed_files"] == 3
    assert data["author"] == "dev"


def test_api_review_endpoint_no_codesage_comments(client, mocker):
    """Tests PR review status endpoint when no CodeSage comments exist."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")
    mocker.patch("app.routes.api.list_issue_comments", return_value=[
        {"id": 100, "body": "Human comment LGTM"}
    ])

    response = client.get("/api/pulls/testowner/testrepo/10/review")
    assert response.status_code == 200
    data = response.json()
    assert data["reviewed"] is False
    assert data["review_count"] == 0
    assert data["latest_review"] is None


def test_api_review_endpoint_with_single_review(client, mocker):
    """Tests PR review status endpoint with one CodeSage review comment."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")
    review_markdown = f"{CODESAGE_REVIEW_MARKER}\n\n## Summary\nOK\n\n## Overall Rating\n**9/10**\n"
    mocker.patch("app.routes.api.list_issue_comments", return_value=[
        {"id": 101, "created_at": "2026-08-01T10:00:00Z", "updated_at": "2026-08-01T10:00:00Z", "body": review_markdown}
    ])

    response = client.get("/api/pulls/testowner/testrepo/10/review")
    assert response.status_code == 200
    data = response.json()
    assert data["reviewed"] is True
    assert data["review_count"] == 1
    assert data["latest_review"]["overall_rating"] == 9
    assert data["latest_review"]["comment_id"] == 101


def test_api_review_endpoint_multiple_reviews_chooses_latest(client, mocker):
    """Tests PR review status endpoint chooses latest review comment when multiple exist."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")
    rev1 = f"{CODESAGE_REVIEW_MARKER}\n## Overall Rating\n**6/10**"
    rev2 = f"{CODESAGE_REVIEW_MARKER}\n## Overall Rating\n**9/10**"

    mocker.patch("app.routes.api.list_issue_comments", return_value=[
        {"id": 101, "created_at": "2026-08-01T10:00:00Z", "updated_at": "2026-08-01T10:00:00Z", "body": rev1},
        {"id": 102, "created_at": "2026-08-02T10:00:00Z", "updated_at": "2026-08-02T10:00:00Z", "body": rev2}
    ])

    response = client.get("/api/pulls/testowner/testrepo/10/review")
    assert response.status_code == 200
    data = response.json()
    assert data["reviewed"] is True
    assert data["review_count"] == 2
    assert data["latest_review"]["comment_id"] == 102
    assert data["latest_review"]["overall_rating"] == 9


def test_dashboard_empty_repository_config(client, mocker):
    """Tests dashboard summary when CODESAGE_REPOSITORIES is empty."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "")

    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["repositories_count"] == 0
    assert data["open_pull_requests"] == 0
    assert data["reviewed_pull_requests"] == 0
    assert data["recent_pull_requests"] == []
    assert data["average_score"] is None


def test_dashboard_aggregation_with_repos(client, mocker):
    """Tests dashboard summary metrics aggregation across monitored repositories."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "owner/repo1")

    rev_comment = f"{CODESAGE_REVIEW_MARKER}\n## Overall Rating\n**8/10**"
    mocker.patch("app.routes.api.list_pull_requests", return_value=[
        {"number": 1, "title": "PR 1", "state": "open"}
    ])
    mocker.patch("app.routes.api.list_issue_comments", return_value=[
        {"id": 1, "created_at": "2026-08-01T00:00:00Z", "body": rev_comment}
    ])

    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["repositories_count"] == 1
    assert data["open_pull_requests"] == 1
    assert data["reviewed_pull_requests"] == 1
    assert data["average_score"] == 8.0


def test_github_failure_produces_safe_api_response(client, mocker):
    """Tests that GitHub REST API failures produce safe HTTP status codes without leaking tokens."""
    mocker.patch("app.config.settings.CODESAGE_REPOSITORIES", "testowner/testrepo")
    mocker.patch("app.routes.api.get_repository", return_value=None)

    response = client.get("/api/repositories/testowner/testrepo")
    assert response.status_code == 404
    assert "not found on GitHub" in response.json()["detail"]


def test_cors_origin_behavior(client):
    """Tests CORS middleware header responses for allowed localhost origin."""
    response = client.options(
        "/api/dashboard",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

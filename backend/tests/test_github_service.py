import pytest
import requests
from unittest.mock import MagicMock
from app.services.github_service import get_pr_files, comment_on_pr, _is_transient_github_error


def test_is_transient_github_error_classification():
    """Tests classification of transient vs permanent GitHub errors."""
    # Transient HTTP errors
    for code in (429, 500, 502, 503, 504):
        err = requests.HTTPError(response=MagicMock(status_code=code))
        assert _is_transient_github_error(err) is True

    # Permanent HTTP errors
    for code in (401, 403, 404):
        err = requests.HTTPError(response=MagicMock(status_code=code))
        assert _is_transient_github_error(err) is False

    # Connection and Timeout errors
    assert _is_transient_github_error(requests.Timeout()) is True
    assert _is_transient_github_error(requests.ConnectionError()) is True


def test_get_pr_files_single_page(mocker):
    """Tests PR file retrieval when all files fit on a single page (<100 files)."""
    mock_get = mocker.patch("requests.get")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"filename": "app/main.py", "status": "modified", "patch": "+ print('hello')"},
        {"filename": "README.md", "status": "added", "patch": "+ # Title"},
    ]
    mock_get.return_value = mock_response

    files = get_pr_files("owner", "repo", 1)
    assert len(files) == 2
    assert files[0]["filename"] == "app/main.py"
    mock_get.assert_called_once()


def test_get_pr_files_pagination_multiple_pages(mocker):
    """Tests that pagination combines multiple pages until <100 items are returned."""
    mock_get = mocker.patch("requests.get")

    page1_data = [{"filename": f"f_{i}.py", "status": "modified", "patch": "diff"} for i in range(100)]
    page2_data = [{"filename": f"f_{i}.py", "status": "added", "patch": "diff"} for i in range(25)]

    res1 = MagicMock(status_code=200)
    res1.json.return_value = page1_data
    res2 = MagicMock(status_code=200)
    res2.json.return_value = page2_data

    mock_get.side_effect = [res1, res2]

    files = get_pr_files("owner", "repo", 1)
    assert len(files) == 125
    assert mock_get.call_count == 2


def test_get_pr_files_empty_first_page(mocker):
    """Tests PR file retrieval when the first page is empty."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = []
    mock_get.return_value = mock_res

    files = get_pr_files("owner", "repo", 1)
    assert files == []
    mock_get.assert_called_once()


def test_get_pr_files_defensive_max_pages(mocker):
    """Tests that get_pr_files respects the defensive max_pages cap."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock(status_code=200)
    # Return 100 items every time
    mock_res.json.return_value = [{"filename": f"f_{i}.py", "status": "modified", "patch": "diff"} for i in range(100)]
    mock_get.return_value = mock_res

    files = get_pr_files("owner", "repo", 1, max_pages=3)
    assert len(files) == 300
    assert mock_get.call_count == 3


def test_comment_on_pr_success(mocker):
    """Tests successful posting of a PR comment."""
    mock_post = mocker.patch("requests.post")
    mock_res = MagicMock()
    mock_res.status_code = 201
    mock_post.return_value = mock_res

    status = comment_on_pr("owner/repo", 42, "Great PR!")
    assert status == 201
    mock_post.assert_called_once()


def test_github_service_permanent_error_no_retry(mocker):
    """Tests that permanent HTTP errors (401 Unauthorized) fail fast without retrying."""
    mock_get = mocker.patch("requests.get")
    mock_res = MagicMock()
    mock_res.status_code = 401
    http_err = requests.HTTPError(response=mock_res)
    mock_res.raise_for_status.side_effect = http_err
    mock_get.return_value = mock_res

    files = get_pr_files("owner", "repo", 1)
    assert files == []
    assert mock_get.call_count == 1

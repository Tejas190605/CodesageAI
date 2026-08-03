import hmac
import hashlib
import json
import pytest
from app.routes.github_webhooks import process_pr


def _sign_payload(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_webhook_invalid_signature_rejected(client):
    """Tests that a webhook request with an invalid signature header returns 401 Unauthorized."""
    response = client.post(
        "/webhook",
        headers={"X-Hub-Signature-256": "sha256=invalidhash123"},
        json={"action": "opened"}
    )
    assert response.status_code == 401


def test_webhook_valid_push_event(client, dummy_secret, mocker):
    """Tests that a valid push webhook event returns 200 OK."""
    mocker.patch("fastapi.BackgroundTasks.add_task")

    payload = {
        "head_commit": {
            "message": "Update README.md",
            "added": ["README.md"],
            "modified": [],
            "removed": []
        }
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    response = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "push",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


def test_webhook_valid_pr_events(client, dummy_secret, mocker):
    """Tests valid PR opened, synchronize, and reopened actions."""
    mocker.patch("fastapi.BackgroundTasks.add_task")

    for action in ("opened", "synchronize", "reopened"):
        payload = {
            "action": action,
            "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
            "pull_request": {"number": 10, "title": "Add feature"}
        }
        body = json.dumps(payload).encode("utf-8")
        sig = _sign_payload(dummy_secret, body)

        response = client.post(
            "/webhook",
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json"
            },
            content=body
        )
        assert response.status_code == 200
        assert response.json() == {"status": "received"}


def test_webhook_ignored_pr_action(client, dummy_secret):
    """Tests that unhandled PR actions (e.g. 'closed', 'labeled') return status='ignored'."""
    payload = {
        "action": "closed",
        "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
        "pull_request": {"number": 10}
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    response = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


def test_process_pr_success_workflow(mocker):
    """Tests complete process_pr success path: get files -> review -> comment."""
    mock_files = [{"filename": "app/main.py", "status": "modified", "patch": "+ code"}]
    mock_review = "## Security Issues\nNone\n## Overall Rating (/10)\n10/10"

    mocker.patch("app.routes.github_webhooks.get_pr_files", return_value=mock_files)
    mocker.patch("app.routes.github_webhooks.review_code", return_value=mock_review)
    mock_comment = mocker.patch("app.routes.github_webhooks.comment_on_pr", return_value=201)

    process_pr("testowner", "testrepo", 15, "Add feature")

    mock_comment.assert_called_once_with(
        repo_full_name="testowner/testrepo",
        pr_number=15,
        comment=mock_review
    )


def test_process_pr_ai_failure_aborts_comment(mocker):
    """Tests that if review_code returns None, comment_on_pr is NOT called."""
    mock_files = [{"filename": "app/main.py", "status": "modified", "patch": "+ code"}]

    mocker.patch("app.routes.github_webhooks.get_pr_files", return_value=mock_files)
    mocker.patch("app.routes.github_webhooks.review_code", return_value=None)
    mock_comment = mocker.patch("app.routes.github_webhooks.comment_on_pr")

    process_pr("testowner", "testrepo", 15, "Add feature")

    mock_comment.assert_not_called()


def test_process_pr_file_retrieval_failure_aborts(mocker):
    """Tests that if get_pr_files returns [], review_code and comment_on_pr are NOT called."""
    mocker.patch("app.routes.github_webhooks.get_pr_files", return_value=[])
    mock_review_code = mocker.patch("app.routes.github_webhooks.review_code")
    mock_comment = mocker.patch("app.routes.github_webhooks.comment_on_pr")

    process_pr("testowner", "testrepo", 15, "Add feature")

    mock_review_code.assert_not_called()
    mock_comment.assert_not_called()

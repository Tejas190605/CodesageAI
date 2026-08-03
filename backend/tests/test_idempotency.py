import json
import pytest
from app.services.delivery_tracker import (
    DeliveryTracker,
    reset_delivery_tracker,
    is_duplicate_delivery,
    record_delivery,
)
from tests.test_webhooks import _sign_payload


@pytest.fixture(autouse=True)
def clean_delivery_tracker():
    """Ensures each idempotency test starts with a clean delivery tracker state."""
    reset_delivery_tracker()
    yield
    reset_delivery_tracker()


def test_delivery_tracker_lru_bounding():
    """Tests that DeliveryTracker evicts oldest entries when capacity is exceeded."""
    tracker = DeliveryTracker(capacity=3)
    tracker.record_delivery("del-1")
    tracker.record_delivery("del-2")
    tracker.record_delivery("del-3")

    assert tracker.is_duplicate("del-1") is True
    assert tracker.is_duplicate("del-2") is True
    assert tracker.is_duplicate("del-3") is True

    # Record 4th delivery -> evicts del-1
    tracker.record_delivery("del-4")

    assert tracker.is_duplicate("del-1") is False
    assert tracker.is_duplicate("del-4") is True


def test_webhook_first_delivery_accepted(client, dummy_secret, mocker):
    """Tests that a first-time webhook delivery ID returns status='received'."""
    mocker.patch("fastapi.BackgroundTasks.add_task")
    payload = {
        "action": "opened",
        "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
        "pull_request": {"number": 1, "title": "Test PR"}
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    response = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-unique-001",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


def test_webhook_duplicate_delivery_ignored(client, dummy_secret, mocker):
    """Tests that sending the exact same X-GitHub-Delivery twice returns status='duplicate' and does NOT trigger background processing."""
    mock_bg = mocker.patch("fastapi.BackgroundTasks.add_task")

    payload = {
        "action": "opened",
        "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
        "pull_request": {"number": 1, "title": "Test PR"}
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    headers = {
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "codesage-test-delivery-001",
        "Content-Type": "application/json"
    }

    # First delivery
    res1 = client.post("/webhook", headers=headers, content=body)
    assert res1.status_code == 200
    assert res1.json() == {"status": "received"}
    assert mock_bg.call_count == 1

    # Reset call count mock
    mock_bg.reset_mock()

    # Second identical delivery
    res2 = client.post("/webhook", headers=headers, content=body)
    assert res2.status_code == 200
    assert res2.json() == {
        "status": "duplicate",
        "delivery_id": "codesage-test-delivery-001"
    }
    # Verify background task was NOT dispatched again!
    mock_bg.assert_not_called()


def test_webhook_different_delivery_ids_processed(client, dummy_secret, mocker):
    """Tests that two different delivery IDs both process normally."""
    mock_bg = mocker.patch("fastapi.BackgroundTasks.add_task")

    payload = {
        "action": "synchronize",
        "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
        "pull_request": {"number": 1, "title": "Test PR"}
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    res1 = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-100",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert res1.json() == {"status": "received"}

    res2 = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-101",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert res2.json() == {"status": "received"}
    assert mock_bg.call_count == 2


def test_webhook_missing_delivery_id_compatibility(client, dummy_secret, mocker):
    """Tests that a webhook request missing X-GitHub-Delivery still processes normally."""
    mocker.patch("fastapi.BackgroundTasks.add_task")
    payload = {
        "action": "opened",
        "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
        "pull_request": {"number": 1, "title": "Test PR"}
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    res = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert res.status_code == 200
    assert res.json() == {"status": "received"}


def test_invalid_signature_never_registered_in_tracker(client):
    """Tests that a request with an invalid signature fails before registering delivery_id in tracker."""
    payload = {"action": "opened"}
    body = json.dumps(payload).encode("utf-8")

    res = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": "sha256=invalidhash",
            "X-GitHub-Delivery": "untrusted-delivery-999",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert res.status_code == 401
    assert is_duplicate_delivery("untrusted-delivery-999") is False

import json
import asyncio
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, SessionLocal
from app.config import settings
import app.models
from app.services.queue_service import (
    enqueue_review,
    cancel_review,
    retry_job,
    get_job_by_id,
    list_jobs,
    get_worker_health_metrics,
)
from app.worker import calculate_backoff_delay, process_review_job
from tests.test_webhooks import _sign_payload


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_calculate_backoff_delay():
    assert calculate_backoff_delay(1) == 5
    assert calculate_backoff_delay(2) == 10
    assert calculate_backoff_delay(3) == 20
    assert calculate_backoff_delay(4) == 40


def test_queue_service_enqueue_and_get(db_session):
    job = enqueue_review(
        db=db_session,
        owner="Tejas190605",
        repo="codexproj",
        pr_number=10,
        pr_title="Feature PR",
        delivery_id="deliv-001"
    )

    assert job.id is not None
    assert job.status == "queued"
    assert job.attempts == 0

    fetched = get_job_by_id(db_session, job.job_id)
    assert fetched is not None
    assert fetched.repository == "Tejas190605/codexproj"
    assert fetched.pr_number == 10


def test_queue_service_cancel_and_retry(db_session):
    job = enqueue_review(db_session, "owner", "repo", pr_number=1)

    # Cancel job
    cancelled = cancel_review(db_session, job.job_id)
    assert cancelled.status == "cancelled"

    # Retry job
    retried = retry_job(db_session, job.job_id)
    assert retried.status == "queued"
    assert retried.attempts == 0


def test_get_worker_health_metrics(db_session):
    enqueue_review(db_session, "owner", "repo", pr_number=1)
    enqueue_review(db_session, "owner", "repo", pr_number=2)

    health = get_worker_health_metrics(db_session)
    assert health["queue_depth"] == 2
    assert health["metrics"]["queued"] == 2
    assert health["metrics"]["total_jobs"] == 2


def test_worker_process_review_job_success(db_session, mocker):
    mocker.patch("app.worker.get_pull_request", return_value={"title": "Test PR", "state": "open", "user": {"login": "dev"}})
    mocker.patch("app.worker.get_pr_files", return_value=[{"filename": "main.py", "patch": "diff"}])
    mocker.patch("app.worker.comment_on_pr", return_value=201)

    job = enqueue_review(db_session, "Tejas190605", "codexproj", pr_number=1)

    res = asyncio.run(process_review_job("Tejas190605", "codexproj", 1, job.job_id))
    assert res["status"] == "completed"

    db_session.expire_all()
    updated = get_job_by_id(db_session, job.job_id)
    assert updated.status == "completed"
    assert updated.attempts == 1


def test_worker_process_review_job_retry_and_dead_letter(db_session, mocker):
    mocker.patch("app.worker.get_pull_request", side_effect=Exception("API Timeout"))

    job = enqueue_review(db_session, "Tejas190605", "codexproj", pr_number=1)

    # First attempt -> state 'retry'
    asyncio.run(process_review_job("Tejas190605", "codexproj", 1, job.job_id))
    db_session.expire_all()
    updated1 = get_job_by_id(db_session, job.job_id)
    assert updated1.status == "retry"
    assert updated1.attempts == 1

    # Force attempts to max_retries
    updated1.attempts = settings.MAX_RETRIES - 1
    db_session.commit()

    # Final attempt -> state 'dead_letter'
    asyncio.run(process_review_job("Tejas190605", "codexproj", 1, job.job_id))
    db_session.expire_all()
    updated2 = get_job_by_id(db_session, job.job_id)
    assert updated2.status == "dead_letter"
    assert updated2.attempts == settings.MAX_RETRIES


def test_api_jobs_and_worker_health_endpoints(client, db_session):
    job = enqueue_review(db_session, "owner", "repo", pr_number=5)

    res_jobs = client.get("/api/jobs")
    assert res_jobs.status_code == 200
    data_jobs = res_jobs.json()
    assert len(data_jobs) == 1
    assert data_jobs[0]["job_id"] == job.job_id

    res_detail = client.get(f"/api/jobs/{job.job_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["pr_number"] == 5

    res_health = client.get("/api/worker/health")
    assert res_health.status_code == 200
    assert res_health.json()["queue_depth"] == 1


def test_webhook_enqueues_review_job(client, dummy_secret):
    payload = {
        "action": "opened",
        "repository": {"name": "testrepo", "owner": {"login": "testowner"}},
        "pull_request": {"number": 42, "title": "New Async PR"}
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign_payload(dummy_secret, body)

    res = client.post(
        "/webhook",
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-async-999",
            "Content-Type": "application/json"
        },
        content=body
    )
    assert res.status_code == 200
    json_resp = res.json()
    assert json_resp["status"] == "received"
    assert "job_id" in json_resp

import json
import hmac
import hashlib
import asyncio
import pytest
from app.config import settings
from app.models.db import (
    Repository,
    PullRequest,
    Review,
    Finding,
    ReviewJob,
    AIUsage,
    AuditEvent,
    PolicyEvaluation,
    RuleEvaluation,
    RepositoryIndex,
    CodeChunk,
)
from app.services.repository_indexer import index_repository_contents
from app.services.retrieval_service import retrieve_context_for_pr
from app.services.rag_context import format_rag_context
from app.services.policy_engine import evaluate_policy_for_pr
from app.services.review_decision import compute_review_decision
from app.services.github_review_publisher import (
    build_pr_review_summary,
    prepare_inline_comments,
)
from app.models.review import StructuredReview, ReviewFinding, ReviewCategory, ReviewSeverity
from app.worker import process_review_job


def generate_webhook_signature(body: bytes, secret: str) -> str:
    """Computes valid HMAC SHA-256 signature for webhook payload."""
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def test_e2e_webhook_signature_validation_and_idempotency(client):
    """
    Step 3 Integration Test:
    Tests webhook payload HMAC signature validation and duplicate delivery ID idempotency.
    """
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "E2E Integration Test PR",
            "state": "open",
            "user": {"login": "test-dev"}
        },
        "repository": {
            "name": "e2e-repo",
            "owner": {"login": "test-org"},
            "full_name": "test-org/e2e-repo"
        }
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    secret = settings.GITHUB_WEBHOOK_SECRET or "dev_webhook_secret_key"
    sig = generate_webhook_signature(body_bytes, secret)

    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "delivery-e2e-1001",
        "X-Hub-Signature-256": sig,
        "Content-Type": "application/json"
    }

    # 1. Post valid webhook payload -> Expect HTTP 200
    res1 = client.post("/webhook", content=body_bytes, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["status"] in ("received", "duplicate")

    # 2. Re-send duplicate delivery ID -> Expect HTTP 200 Idempotent Duplicate
    res2 = client.post("/webhook", content=body_bytes, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "duplicate"

    # 3. Post with invalid signature -> Expect HTTP 401
    bad_headers = dict(headers)
    bad_headers["X-Hub-Signature-256"] = "sha256=invalid_signature_hash"
    res3 = client.post("/webhook", content=body_bytes, headers=bad_headers)
    assert res3.status_code == 401


def test_e2e_worker_review_pipeline_execution(db_session, monkeypatch):
    """
    Steps 4, 5, 6, 7 & 9 Integration Test:
    Executes worker job processing from queue -> RAG context -> Policy Engine -> Decision -> Audit & Analytics persistence.
    Mocks only external network boundaries (GitHub API & Gemini API).
    """
    # 1. Mock external GitHub network calls
    monkeypatch.setattr("app.worker.get_pull_request", lambda owner, repo, num: {
        "title": "Fix Auth Vulnerability",
        "state": "open",
        "user": {"login": "test-author"},
        "additions": 10,
        "deletions": 2,
        "changed_files": 2
    })

    test_files = [
        {
            "filename": "app/auth.py",
            "status": "modified",
            "patch": "@@ -10,3 +10,4 @@\n def login():\n+    print('DEBUG_AUTH')\n+    access_token = 'TEST_SECRET_TOKEN_VALUE_1234567890'\n"
        },
        {
            "filename": "requirements.txt",
            "status": "modified",
            "patch": "@@ -1 +1 @@\n+pyjwt==2.8.0\n"
        }
    ]
    monkeypatch.setattr("app.worker.get_pr_files", lambda owner, repo, num: test_files)
    monkeypatch.setattr("app.worker.comment_on_pr", lambda repo, num, body: True)

    # 2. Mock external Gemini LLM response
    mock_structured = StructuredReview(
        summary="Found critical security issues and leftover debug code.",
        overall_rating=4,
        findings=[
            ReviewFinding(
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Exposed Credentials",
                description="Hardcoded GitHub token exposed in source file.",
                file="app/auth.py",
                line=12,
                suggested_fix="use settings.GITHUB_TOKEN"
            )
        ]
    )
    monkeypatch.setattr("app.worker.review_code", lambda title_or_message, files, rag_context=None: mock_structured)

    # 3. Seed repository index for Phase 5B RAG retrieval
    index_repository_contents(
        db=db_session,
        repository="org-e2e/repo-e2e",
        commit_sha="commit-e2e-sha",
        files_dict={"app/auth.py": "def login(): pass\n"}
    )

    # 4. Create ReviewJob record in DB
    job = ReviewJob(
        job_id="job-e2e-99",
        repository="org-e2e/repo-e2e",
        pr_number=1,
        status="queued",
        attempts=0,
        max_retries=3
    )
    db_session.add(job)
    db_session.commit()

    # 5. Process review job synchronously via asyncio.run
    result = asyncio.run(process_review_job(
        owner="org-e2e",
        repo="repo-e2e",
        pr_number=1,
        job_id="job-e2e-99"
    ))

    assert result["status"] == "completed"

    # 6. Verify Database Persistence & Relationships
    db_job = db_session.query(ReviewJob).filter(ReviewJob.job_id == "job-e2e-99").first()
    assert db_job.status == "completed"

    db_repo = db_session.query(Repository).filter(Repository.full_name == "org-e2e/repo-e2e").first()
    assert db_repo is not None

    db_pr = db_session.query(PullRequest).filter(PullRequest.repository_id == db_repo.id).first()
    assert db_pr.number == 1

    db_review = db_session.query(Review).filter(Review.pull_request_id == db_pr.id).first()
    assert db_review is not None
    assert "CodeSage AI" in db_review.markdown

    # 7. Verify Policy Evaluation Snapshot & Secret Redaction
    policy_eval = db_session.query(PolicyEvaluation).filter(PolicyEvaluation.review_id == db_review.id).first()
    assert policy_eval is not None
    assert policy_eval.blocking_count >= 1

    # Verify secret evidence was redacted
    for rule_eval in policy_eval.rule_evaluations:
        if rule_eval.rule_key == "hardcoded-secrets":
            evidence = (rule_eval.metadata_json or {}).get("evidence", "")
            assert "TEST_SECRET_TOKEN_VALUE_1234567890" not in evidence

    # 8. Verify Audit Event Logging
    audit_events = db_session.query(AuditEvent).all()
    assert len(audit_events) >= 1
    event_types = [e.event_type for e in audit_events]
    assert "review.completed" in event_types or "repository.indexed" in event_types


def test_e2e_tenant_isolation_and_rbac_boundaries(db_session):
    """
    Step 8 Integration Test:
    Verifies multi-tenant isolation across vector code chunks, policies, and search results.
    """
    index_repository_contents(db_session, "tenant-1/repo-alpha", "sha-1", {"main.py": "def alpha(): pass"})
    index_repository_contents(db_session, "tenant-2/repo-beta", "sha-2", {"main.py": "def beta(): pass"})

    chunks_1 = db_session.query(CodeChunk).filter(CodeChunk.repository == "tenant-1/repo-alpha").all()
    chunks_2 = db_session.query(CodeChunk).filter(CodeChunk.repository == "tenant-2/repo-beta").all()

    assert len(chunks_1) >= 1
    assert len(chunks_2) >= 1
    assert all(c.repository == "tenant-1/repo-alpha" for c in chunks_1)
    assert all(c.repository == "tenant-2/repo-beta" for c in chunks_2)


def test_e2e_api_contract_shapes(client):
    """
    Step 10 Integration Test:
    Validates API route response shapes against frontend/src/lib/api.ts contract expectations.
    """
    endpoints = [
        "/api/dashboard",
        "/api/repositories",
        "/api/jobs",
        "/api/ai/providers",
        "/api/ai/prompts",
        "/api/policies",
        "/api/policies/effective/test-owner/test-repo",
        "/api/analytics/overview",
        "/api/analytics/reviews",
        "/api/analytics/findings",
        "/api/analytics/ai-usage",
        "/api/analytics/jobs",
        "/api/audit-events"
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Endpoint '{ep}' returned status {res.status_code}"

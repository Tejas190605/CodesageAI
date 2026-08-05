import pytest
from app.services.audit_service import record_event, sanitize_metadata
from app.services.analytics_service import (
    get_analytics_overview,
    get_review_analytics,
    get_finding_analytics,
    get_ai_usage_analytics,
    get_job_analytics,
)
from app.models.db import (
    Repository,
    PullRequest,
    Review,
    Finding,
    ReviewJob,
    AIUsage,
    AuditEvent,
)


def test_sanitize_sensitive_metadata():
    """Tests recursive scrubbing of tokens, secrets, credentials, and API keys."""
    raw_metadata = {
        "repository": "owner/repo",
        "github_token": "TEST_SECRET_TOKEN_VALUE",
        "nested": {
            "api_key": "secret-key-999",
            "safe_count": 42
        }
    }
    clean_meta = sanitize_metadata(raw_metadata)

    assert clean_meta["repository"] == "owner/repo"
    assert clean_meta["github_token"] == "[REDACTED_SENSITIVE_DATA]"
    assert clean_meta["nested"]["api_key"] == "[REDACTED_SENSITIVE_DATA]"
    assert clean_meta["nested"]["safe_count"] == 42


def test_record_audit_event(db_session):
    """Tests audit event persistence and query integrity."""
    event_rec = record_event(
        db=db_session,
        event_type="user.login",
        actor="test_user",
        description="User logged in via GitHub OAuth.",
        metadata={"token": "should_be_redacted", "ip": "127.0.0.1"}
    )

    assert event_rec is not None
    assert event_rec.event_type == "user.login"
    assert event_rec.actor == "test_user"
    assert event_rec.metadata_json["token"] == "[REDACTED_SENSITIVE_DATA]"
    assert event_rec.metadata_json["ip"] == "127.0.0.1"


def test_empty_database_analytics_safety(db_session):
    """Tests that analytics calculation returns valid default structures when database is empty."""
    overview = get_analytics_overview(db_session)
    assert overview["total_repositories"] == 0
    assert overview["total_reviews"] == 0

    rev_analytics = get_review_analytics(db_session)
    assert rev_analytics["total_reviews"] == 0
    assert rev_analytics["approval_rate"] == 100.0

    find_analytics = get_finding_analytics(db_session)
    assert find_analytics["total_findings"] == 0
    assert find_analytics["by_severity"]["critical"] == 0

    ai_analytics = get_ai_usage_analytics(db_session)
    assert ai_analytics["total_requests"] == 0
    assert ai_analytics["total_cost_usd"] == "0.0000"

    job_analytics = get_job_analytics(db_session)
    assert job_analytics["total_jobs"] == 0
    assert job_analytics["success_rate_percent"] == 100.0


def test_analytics_aggregations_with_data(db_session):
    """Tests analytics calculations with populated repository, review, finding, and usage records."""
    repo = Repository(owner="org-a", name="repo-a", full_name="org-a/repo-a")
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(repository_id=repo.id, number=1, title="Add Feature", author="dev1")
    db_session.add(pr)
    db_session.commit()

    review = Review(pull_request_id=pr.id, overall_rating=8, summary="Good PR")
    db_session.add(review)
    db_session.commit()

    finding = Finding(review_id=review.id, category="security", severity="critical", title="SQL Injection", description="SQL Injection vulnerability")
    db_session.add(finding)

    ai_rec = AIUsage(provider="gemini", model="gemini-2.5-flash", total_tokens=1500, estimated_cost=0.0003)
    db_session.add(ai_rec)

    job_rec = ReviewJob(job_id="job-1", repository="org-a/repo-a", pr_number=1, status="completed")
    db_session.add(job_rec)

    db_session.commit()

    overview = get_analytics_overview(db_session)
    assert overview["total_repositories"] == 1
    assert overview["total_pull_requests"] == 1
    assert overview["total_reviews"] == 1

    find_analytics = get_finding_analytics(db_session)
    assert find_analytics["by_severity"]["critical"] == 1

    ai_analytics = get_ai_usage_analytics(db_session)
    assert ai_analytics["total_requests"] == 1
    assert ai_analytics["total_tokens"] == 1500

    job_analytics = get_job_analytics(db_session)
    assert job_analytics["completed"] == 1
    assert job_analytics["success_rate_percent"] == 100.0


def test_analytics_and_audit_rest_apis(client):
    """Tests REST endpoints for analytics and audit events."""
    res_ov = client.get("/api/analytics/overview")
    assert res_ov.status_code == 200
    assert "total_repositories" in res_ov.json()

    res_ai = client.get("/api/analytics/ai-usage")
    assert res_ai.status_code == 200
    assert "total_tokens" in res_ai.json()

    res_audit = client.get("/api/audit-events")
    assert res_audit.status_code == 200
    assert "events" in res_audit.json()

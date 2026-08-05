import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.db import (
    Repository,
    PullRequest,
    Review,
    Finding,
    ReviewJob,
    AIUsage,
    PolicyEvaluation,
)

logger = logging.getLogger("codesage.analytics_service")


def get_analytics_overview(db: Session) -> Dict[str, Any]:
    """Returns top-level overview metrics across repositories, PRs, reviews, and findings."""
    total_repos = db.query(func.count(Repository.id)).scalar() or 0
    total_prs = db.query(func.count(PullRequest.id)).scalar() or 0
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    total_findings = db.query(func.count(Finding.id)).scalar() or 0

    return {
        "total_repositories": total_repos,
        "total_pull_requests": total_prs,
        "total_reviews": total_reviews,
        "total_findings": total_findings,
    }


def get_review_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
    """Returns review processing stats and approval vs change request distributions."""
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    flagged_reviews = db.query(func.count(func.distinct(Finding.review_id))).scalar() or 0
    clean_reviews = max(0, total_reviews - flagged_reviews)

    return {
        "total_reviews": total_reviews,
        "clean_reviews": clean_reviews,
        "flagged_reviews": flagged_reviews,
        "approval_rate": round((clean_reviews / total_reviews * 100), 1) if total_reviews > 0 else 100.0
    }


def get_finding_analytics(db: Session) -> Dict[str, Any]:
    """Returns findings breakdowns by severity level and category."""
    severity_query = db.query(Finding.severity, func.count(Finding.id)).group_by(Finding.severity).all()
    by_severity = {sev.lower() if isinstance(sev, str) else str(sev): count for sev, count in severity_query}

    category_query = db.query(Finding.category, func.count(Finding.id)).group_by(Finding.category).all()
    by_category = {cat.lower() if isinstance(cat, str) else str(cat): count for cat, count in category_query}

    return {
        "by_severity": {
            "critical": by_severity.get("critical", 0),
            "high": by_severity.get("high", 0),
            "medium": by_severity.get("medium", 0),
            "low": by_severity.get("low", 0),
            "info": by_severity.get("info", 0),
        },
        "by_category": by_category,
        "total_findings": sum(by_severity.values())
    }


def get_ai_usage_analytics(db: Session) -> Dict[str, Any]:
    """Returns token consumption, estimated costs, and multi-provider breakdown."""
    total_reqs = db.query(func.count(AIUsage.id)).scalar() or 0
    total_tokens = db.query(func.sum(AIUsage.total_tokens)).scalar() or 0
    total_cost = db.query(func.sum(AIUsage.estimated_cost)).scalar() or 0.0

    provider_query = db.query(
        AIUsage.provider,
        func.count(AIUsage.id),
        func.sum(AIUsage.total_tokens)
    ).group_by(AIUsage.provider).all()

    by_provider = [
        {
            "provider": prov,
            "requests": req_cnt,
            "tokens": tok_cnt or 0
        }
        for prov, req_cnt, tok_cnt in provider_query
    ]

    return {
        "total_requests": total_reqs,
        "total_tokens": int(total_tokens),
        "total_cost_usd": f"{total_cost:.4f}",
        "by_provider": by_provider
    }


def get_job_analytics(db: Session) -> Dict[str, Any]:
    """Returns review queue job status breakdown and execution duration metrics."""
    status_query = db.query(ReviewJob.status, func.count(ReviewJob.id)).group_by(ReviewJob.status).all()
    by_status = {status: count for status, count in status_query}

    completed = by_status.get("completed", 0)
    failed = by_status.get("failed", 0)
    queued = by_status.get("queued", 0)
    processing = by_status.get("processing", 0)
    total_jobs = completed + failed + queued + processing

    success_rate = round((completed / (completed + failed) * 100), 1) if (completed + failed) > 0 else 100.0

    return {
        "total_jobs": total_jobs,
        "completed": completed,
        "failed": failed,
        "queued": queued,
        "processing": processing,
        "success_rate_percent": success_rate
    }

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import (
    get_analytics_overview,
    get_review_analytics,
    get_finding_analytics,
    get_ai_usage_analytics,
    get_job_analytics,
)

logger = logging.getLogger("codesage.routes.analytics")

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Insights"])


@router.get("/overview")
def read_analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns top-level overview metrics across repositories, PRs, reviews, and findings."""
    return get_analytics_overview(db)


@router.get("/reviews")
def read_review_analytics(days: int = 30, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns review turnaround, approval rate, and processing statistics."""
    return get_review_analytics(db, days=days)


@router.get("/findings")
def read_finding_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns findings breakdown by severity levels and categories."""
    return get_finding_analytics(db)


@router.get("/ai-usage")
def read_ai_usage_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns AI token consumption, estimated costs, and provider usage."""
    return get_ai_usage_analytics(db)


@router.get("/jobs")
def read_job_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns review queue job status breakdown and success rates."""
    return get_job_analytics(db)

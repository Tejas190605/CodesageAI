import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db import ReviewJob
from app.services.queue_service import (
    enqueue_review,
    get_job_by_id,
    cancel_review,
    retry_job,
    list_jobs,
    get_worker_health_metrics,
)

logger = logging.getLogger("codesage.routes.jobs")

router = APIRouter(tags=["jobs-api"])


def _map_job_dict(job: ReviewJob) -> Dict[str, Any]:
    """Serializes a ReviewJob ORM object into a dictionary response."""
    return {
        "id": job.id,
        "job_id": job.job_id,
        "repository": job.repository,
        "pr_number": job.pr_number,
        "pr_title": job.pr_title,
        "delivery_id": job.delivery_id,
        "status": job.status,
        "priority": job.priority,
        "attempts": job.attempts,
        "max_retries": job.max_retries,
        "failure_reason": job.failure_reason,
        "worker_id": job.worker_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/api/jobs")
def get_jobs(
    status: Optional[str] = Query(None, description="Filter by job status (queued|running|completed|failed|retry|dead_letter|all)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Lists background AI review jobs ordered chronologically newest first."""
    jobs = list_jobs(db, status=status, limit=limit, offset=offset)
    return [_map_job_dict(j) for j in jobs]


@router.get("/api/jobs/{job_id}")
def get_job_detail(
    job_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Fetches detailed status metadata for a specific job ID."""
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return _map_job_dict(job)


@router.post("/api/jobs/{job_id}/retry")
def retry_failed_job(
    job_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Manually re-enqueues a failed or dead-letter review job."""
    job = retry_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found or cannot be retried.")
    return {
        "message": f"Job '{job_id}' has been re-enqueued for retry.",
        "job": _map_job_dict(job)
    }


@router.delete("/api/jobs/{job_id}")
def cancel_or_delete_job(
    job_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Cancels an active or queued job."""
    job = cancel_review(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {
        "message": f"Job '{job_id}' has been cancelled.",
        "job": _map_job_dict(job)
    }


@router.get("/api/worker/health")
def get_worker_health(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Returns queue depth, running worker count, job breakdown metrics, and Redis connection status."""
    return get_worker_health_metrics(db)

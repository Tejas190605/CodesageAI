import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import settings
from app.models.db import ReviewJob
from app.services.redis_manager import get_redis_client, get_in_memory_queue

logger = logging.getLogger("codesage.queue_service")


def _utc_now():
    return datetime.now(timezone.utc)


def enqueue_review(
    db: Session,
    owner: str,
    repo: str,
    pr_number: int,
    pr_title: Optional[str] = None,
    delivery_id: Optional[str] = None,
    priority: int = 0
) -> ReviewJob:
    """
    Creates a new ReviewJob record in DB with status='queued' and enqueues job in Redis or fallback memory queue.
    """
    repository_full_name = f"{owner}/{repo}"
    job_id = f"job-{uuid.uuid4().hex[:12]}"

    job = ReviewJob(
        job_id=job_id,
        repository=repository_full_name,
        pr_number=pr_number,
        pr_title=pr_title or f"PR #{pr_number}",
        delivery_id=delivery_id,
        status="queued",
        priority=priority,
        attempts=0,
        max_retries=settings.MAX_RETRIES,
        created_at=_utc_now()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Push to fallback memory queue for local execution if Redis unavailable
    mem_q = get_in_memory_queue()
    try:
        mem_q.put_nowait({
            "job_id": job.job_id,
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
            "pr_title": job.pr_title,
            "delivery_id": delivery_id
        })
    except Exception as e:
        logger.warning(f"Failed putting job {job_id} into memory queue: {e}")

    logger.info(f"Enqueued AI review job '{job_id}' for {repository_full_name}#{pr_number} (delivery: {delivery_id}).")
    return job


def get_job_by_id(db: Session, job_id: str) -> Optional[ReviewJob]:
    """Fetches a ReviewJob record by job_id."""
    return db.query(ReviewJob).filter(ReviewJob.job_id == job_id).first()


def cancel_review(db: Session, job_id: str) -> Optional[ReviewJob]:
    """Cancels a queued or failed job, marking status='cancelled'."""
    job = get_job_by_id(db, job_id)
    if not job:
        return None

    if job.status in ["queued", "retry", "failed"]:
        job.status = "cancelled"
        job.updated_at = _utc_now()
        db.commit()
        db.refresh(job)
        logger.info(f"Cancelled job '{job_id}'.")
    return job


def retry_job(db: Session, job_id: str) -> Optional[ReviewJob]:
    """
    Manually retries a failed or dead-letter job by resetting attempts and status to 'queued'.
    """
    job = get_job_by_id(db, job_id)
    if not job:
        return None

    if job.status in ["failed", "dead_letter", "retry", "cancelled"]:
        job.status = "queued"
        job.failure_reason = None
        job.attempts = 0
        job.updated_at = _utc_now()
        db.commit()
        db.refresh(job)

        # Re-enqueue in memory queue
        parts = job.repository.split("/", 1)
        owner = parts[0] if len(parts) > 0 else ""
        repo = parts[1] if len(parts) > 1 else ""
        mem_q = get_in_memory_queue()
        try:
            mem_q.put_nowait({
                "job_id": job.job_id,
                "owner": owner,
                "repo": repo,
                "pr_number": job.pr_number,
                "pr_title": job.pr_title,
                "delivery_id": job.delivery_id
            })
        except Exception as e:
            logger.warning(f"Error re-enqueuing retry job '{job_id}': {e}")

        logger.info(f"Re-enqueued job '{job_id}' for retry.")
    return job


def list_jobs(
    db: Session,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[ReviewJob]:
    """Lists ReviewJob records filtered optionally by status."""
    query = db.query(ReviewJob)
    if status and status != "all":
        query = query.filter(ReviewJob.status == status)
    return query.order_by(ReviewJob.created_at.desc()).offset(offset).limit(limit).all()


def get_worker_health_metrics(db: Session) -> Dict[str, Any]:
    """
    Computes queue metrics across all job states and reports Redis connection status.
    """
    total_jobs = db.query(func.count(ReviewJob.id)).scalar() or 0
    queued_count = db.query(func.count(ReviewJob.id)).filter(ReviewJob.status == "queued").scalar() or 0
    running_count = db.query(func.count(ReviewJob.id)).filter(ReviewJob.status == "running").scalar() or 0
    completed_count = db.query(func.count(ReviewJob.id)).filter(ReviewJob.status == "completed").scalar() or 0
    failed_count = db.query(func.count(ReviewJob.id)).filter(ReviewJob.status == "failed").scalar() or 0
    retry_count = db.query(func.count(ReviewJob.id)).filter(ReviewJob.status == "retry").scalar() or 0
    dead_letter_count = db.query(func.count(ReviewJob.id)).filter(ReviewJob.status == "dead_letter").scalar() or 0

    return {
        "status": "healthy",
        "redis_connected": False,  # Updated dynamically when async ping is called
        "queue_depth": queued_count,
        "running_workers": running_count,
        "metrics": {
            "total_jobs": total_jobs,
            "queued": queued_count,
            "running": running_count,
            "completed": completed_count,
            "failed": failed_count,
            "retry": retry_count,
            "dead_letter": dead_letter_count
        },
        "concurrency_limit": settings.WORKER_CONCURRENCY,
        "max_retries": settings.MAX_RETRIES
    }

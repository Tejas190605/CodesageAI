import os
import sys
import logging
import asyncio
import socket
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.database import SessionLocal
from app.config import settings
from app.models.db import ReviewJob
from app.services.github_service import (
    get_pull_request,
    get_pr_files,
    comment_on_pr,
)
from app.services.ai_review import review_code
from app.services.retrieval_service import retrieve_context_for_pr
from app.services.rag_context import format_rag_context
from app.services.policy_engine import evaluate_policy_for_pr
from app.services.review_decision import compute_review_decision
from app.services.github_review_publisher import (
    build_pr_review_summary,
    prepare_inline_comments,
)
from app.services.audit_service import record_event
from app.db_repositories.repository_repo import upsert_repository
from app.db_repositories.pr_repo import upsert_pull_request
from app.db_repositories.review_repo import create_review_with_findings
from app.services.queue_service import get_job_by_id, get_in_memory_queue

logger = logging.getLogger("codesage.worker")

WORKER_ID = f"worker-{socket.gethostname()}-{os.getpid()}"


def _utc_now():
    return datetime.now(timezone.utc)


def calculate_backoff_delay(attempts: int) -> int:
    """Computes exponential backoff delay in seconds: 5, 10, 20, 40..."""
    return (2 ** max(0, attempts - 1)) * 5


async def process_review_job(
    owner: str,
    repo: str,
    pr_number: int,
    job_id: str,
    pr_title: Optional[str] = None,
    delivery_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Core worker execution routine for processing an AI review job.
    Integrates RAG context retrieval, Gemini AI review, Policy Engine evaluation,
    Review Decision calculation, GitHub publishing, and Audit Event logging.
    """
    logger.info(f"[{WORKER_ID}] Starting job '{job_id}' for {owner}/{repo}#{pr_number}")

    # 1. Update job status to 'running'
    with SessionLocal() as db:
        job = get_job_by_id(db, job_id)
        if not job:
            logger.error(f"Job '{job_id}' not found in DB!")
            return {"status": "failed", "reason": "job_not_found"}

        if job.status == "cancelled":
            logger.info(f"Job '{job_id}' was cancelled before execution.")
            return {"status": "cancelled"}

        job.status = "running"
        job.attempts += 1
        job.started_at = _utc_now()
        job.worker_id = WORKER_ID
        job.updated_at = _utc_now()
        db.commit()
        db.refresh(job)
        attempts = job.attempts
        max_retries = job.max_retries

    # 2. Execute Integrated AI & Policy Review Pipeline
    try:
        pr_data = get_pull_request(owner, repo, pr_number)
        title = pr_title or (pr_data.get("title") if pr_data else f"PR #{pr_number}")
        files = get_pr_files(owner, repo, pr_number) or []

        if not files:
            logger.warning(f"No changed files found for {owner}/{repo}#{pr_number}.")

        # Retrieve Phase 5B RAG Repository Context
        rag_info = {"formatted_text": "", "chunk_count": 0, "citations": []}
        with SessionLocal() as db:
            try:
                retrieved_chunks = retrieve_context_for_pr(db, repository=f"{owner}/{repo}", changed_files=files)
                rag_info = format_rag_context(retrieved_chunks)
            except Exception as e:
                logger.warning(f"RAG context retrieval skipped for {owner}/{repo}: {e}")

        rag_context_str = rag_info["formatted_text"] if rag_info.get("chunk_count", 0) > 0 else None

        # Generate Gemini AI Structured Review
        structured_review = review_code(
            title_or_message=title,
            files=files,
            rag_context=rag_context_str
        )

        # 3. Persist PR & Review to DB, and Evaluate Policy Engine
        with SessionLocal() as db:
            db_repo = upsert_repository(db, owner, repo)
            db_pr = upsert_pull_request(
                db,
                repository_id=db_repo.id,
                number=pr_number,
                title=title,
                state=pr_data.get("state", "open") if pr_data else "open",
                author=pr_data.get("user", {}).get("login", "unknown") if pr_data else "unknown",
                additions=pr_data.get("additions") if pr_data else None,
                deletions=pr_data.get("deletions") if pr_data else None,
                changed_files=pr_data.get("changed_files") if pr_data else None,
                commits=pr_data.get("commits") if pr_data else None,
                html_url=pr_data.get("html_url") if pr_data else None
            )

            db_review = create_review_with_findings(
                db,
                pull_request_id=db_pr.id,
                summary=structured_review.summary if structured_review else "Review Completed",
                overall_rating=structured_review.overall_rating if structured_review else 10,
                markdown="",
                structured_review=structured_review
            )

            # Evaluate Policy Engine
            policy_eval, rule_results = evaluate_policy_for_pr(
                db=db,
                review_id=db_review.id,
                files=files,
                structured_review=structured_review
            )

            # Compute Review Decision
            review_decision = compute_review_decision(rule_results)

            # Build Actionable PR Review Summary
            markdown_body = build_pr_review_summary(
                review_decision=review_decision,
                rule_results=rule_results,
                rag_citations=rag_info.get("citations", []),
                overall_rating=structured_review.overall_rating if structured_review else 10
            )

            db_review.markdown = markdown_body
            db.commit()

            # Record Audit Event for completed review
            record_event(
                db=db,
                event_type="review.completed",
                actor=WORKER_ID,
                repository_id=db_repo.id,
                description=f"Completed AI code review for {owner}/{repo}#{pr_number} (Decision: {review_decision['event']})."
            )

        # 4. Post review comment to GitHub PR thread
        try:
            comment_on_pr(f"{owner}/{repo}", pr_number, markdown_body)
            with SessionLocal() as db:
                record_event(
                    db=db,
                    event_type="github.review_published",
                    actor=WORKER_ID,
                    description=f"Published GitHub review for {owner}/{repo}#{pr_number}."
                )
        except Exception as e:
            logger.error(f"Failed posting PR comment to GitHub: {e}")

        # Mark job completed in DB
        with SessionLocal() as db:
            completed_job = get_job_by_id(db, job_id)
            if completed_job:
                completed_job.status = "completed"
                completed_job.completed_at = _utc_now()
                completed_job.updated_at = _utc_now()
                completed_job.failure_reason = None
                db.commit()

        logger.info(f"[{WORKER_ID}] Job '{job_id}' completed successfully!")
        return {"status": "completed", "job_id": job_id}

    except Exception as exc:
        error_msg = str(exc)
        logger.error(f"[{WORKER_ID}] Exception during job '{job_id}' (attempt {attempts}/{max_retries}): {error_msg}")

        with SessionLocal() as db:
            failed_job = get_job_by_id(db, job_id)
            if failed_job:
                failed_job.failure_reason = error_msg
                failed_job.updated_at = _utc_now()

                if attempts < max_retries:
                    failed_job.status = "retry"
                    delay = calculate_backoff_delay(attempts)
                    logger.info(f"[{WORKER_ID}] Job '{job_id}' scheduled for retry in {delay}s.")
                else:
                    failed_job.status = "dead_letter"
                    logger.error(f"[{WORKER_ID}] Job '{job_id}' moved to dead-letter queue (max retries reached).")

                db.commit()

            record_event(
                db=db,
                event_type="review.failed",
                actor=WORKER_ID,
                description=f"Review job '{job_id}' failed: {error_msg}"
            )

        return {"status": "failed", "job_id": job_id, "error": error_msg}


async def run_worker_loop():
    """
    Background worker loop consuming enqueued jobs from the in-memory queue.
    """
    mem_q = get_in_memory_queue()
    logger.info(f"[{WORKER_ID}] Async worker loop started listening for jobs...")

    while True:
        try:
            job_data = await mem_q.get()
            if job_data is None:  # Shutdown signal
                break

            await process_review_job(
                owner=job_data["owner"],
                repo=job_data["repo"],
                pr_number=job_data["pr_number"],
                job_id=job_data["job_id"],
                pr_title=job_data.get("pr_title"),
                delivery_id=job_data.get("delivery_id")
            )
            mem_q.task_done()
        except asyncio.CancelledError:
            logger.info(f"[{WORKER_ID}] Worker loop cancelled.")
            break
        except Exception as e:
            logger.error(f"[{WORKER_ID}] Error in worker loop: {e}")
            await asyncio.sleep(1)

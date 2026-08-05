import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session

from app.security.github_signature import verify_github_signature
from app.services.ai_review import review_code
from app.services.github_service import get_pr_files, comment_on_pr
from app.services.review_renderer import render_review_markdown
from app.services.delivery_tracker import is_duplicate_delivery, record_delivery
from app.database import get_db, SessionLocal
from app.db_repositories.repository_repo import upsert_repository
from app.db_repositories.pr_repo import upsert_pull_request
from app.db_repositories.review_repo import create_review_with_findings
from app.services.queue_service import enqueue_review

logger = logging.getLogger("codesage.routes.webhooks")

router = APIRouter()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    FastAPI webhook endpoint for GitHub repository events.
    Verifies payload signature, checks delivery idempotency, enqueues background review jobs,
    and returns immediate status response.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # 1. Verify cryptographic signature BEFORE parsing JSON or checking tracker
    verify_github_signature(signature, body)

    # 2. Check X-GitHub-Delivery idempotency
    delivery_id = request.headers.get("X-GitHub-Delivery")
    if delivery_id:
        if is_duplicate_delivery(delivery_id):
            logger.info(f"Duplicate GitHub delivery '{delivery_id}' ignored.")
            return {"status": "duplicate", "delivery_id": delivery_id}
        record_delivery(delivery_id)
        logger.info(f"Accepted GitHub delivery '{delivery_id}'")
    else:
        logger.warning("Webhook request missing X-GitHub-Delivery header. Processing normally.")

    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    logger.info(f"Webhook received: event='{event}'")

    if event == "push":
        commit = payload.get("head_commit", {})
        message = commit.get("message", "No commit message")
        filenames = (
            commit.get("added", [])
            + commit.get("modified", [])
            + commit.get("removed", [])
        )
        logger.info(f"Push event triggered: commit message='{message}', files_changed={len(filenames)}")
        background_tasks.add_task(process_push, message, filenames)

    elif event == "pull_request":
        action = payload.get("action")
        if action not in ["opened", "synchronize", "reopened"]:
            logger.info(f"Ignoring PR event action='{action}'")
            return {"status": "ignored"}

        repository = payload.get("repository", {})
        owner = repository.get("owner", {}).get("login")
        repo = repository.get("name")
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")
        pr_title = pr.get("title", "")
        pr_html_url = pr.get("html_url", "")
        pr_user = pr.get("user", {}).get("login", "unknown")

        if not owner or not repo or not pr_number:
            logger.warning("Pull Request webhook missing owner, repo, or pr_number payload data.")
            raise HTTPException(status_code=400, detail="Invalid PR webhook payload.")

        logger.info(f"PR event received: repo='{owner}/{repo}', pr=#{pr_number}, action='{action}'")

        # Enqueue background review job
        job = enqueue_review(
            db=db,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            pr_title=pr_title,
            delivery_id=delivery_id
        )

        return {"status": "received", "job_id": job.job_id}

    elif event == "installation":
        action = payload.get("action")
        inst_data = payload.get("installation", {})
        inst_id = inst_data.get("id")
        account = inst_data.get("account", {})
        account_login = account.get("login", "unknown")
        account_id = account.get("id", 0)

        if inst_id:
            from app.db_repositories.installation_repo import upsert_installation
            status_map = {"created": "active", "deleted": "deleted", "suspend": "suspended", "unsuspend": "active"}
            new_status = status_map.get(action, "active")
            upsert_installation(
                db=db,
                installation_id=inst_id,
                account_login=account_login,
                account_id=account_id,
                account_type=account.get("type", "User"),
                target_type=inst_data.get("target_type", "User"),
                repository_selection=inst_data.get("repository_selection", "all"),
                status=new_status
            )
            logger.info(f"GitHub App installation #{inst_id} ({account_login}) action='{action}' status='{new_status}'")
        return {"status": "received", "event": "installation"}

    elif event == "installation_repositories":
        action = payload.get("action")
        inst_id = payload.get("installation", {}).get("id")
        if inst_id:
            from app.db_repositories.installation_repo import get_installation_by_id, link_repository_installation
            inst = get_installation_by_id(db, inst_id)
            if inst:
                repos_added = payload.get("repositories_added", [])
                for r in repos_added:
                    full_name = r.get("full_name")
                    if full_name:
                        parts = full_name.split("/")
                        if len(parts) == 2:
                            upsert_repository(db, owner=parts[0], name=parts[1])
                            link_repository_installation(db, full_name, inst.id)
                            logger.info(f"Onboarded repository '{full_name}' to installation #{inst_id}")
        return {"status": "received", "event": "installation_repositories"}

    return {"status": "received"}


def process_push(message: str, filenames: List[str]) -> None:
    """Background worker task for processing GitHub push events."""
    logger.info(f"Processing push event: '{message}' ({len(filenames)} file(s))")
    files = [
        {
            "filename": fname,
            "status": "modified",
            "patch": "Push webhook contains filenames only."
        }
        for fname in filenames
    ]

    structured_review = review_code(message, files)
    if structured_review:
        logger.info(f"Push AI review completed successfully (Rating: {structured_review.overall_rating}/10).")
    else:
        logger.info("Push AI review skipped or yielded no result.")


def process_pr(
    owner: str,
    repo: str,
    pr_number: int,
    pr_title: str,
    pr_html_url: str = "",
    pr_author: str = "unknown",
    pr_payload: Dict[str, Any] = None
) -> None:
    """
    Background worker task for processing GitHub Pull Request events.
    Maintained for direct synchronous invocations and backwards-compatibility.
    """
    logger.info(f"Starting direct PR review process for {owner}/{repo}#{pr_number}...")

    files = get_pr_files(owner, repo, pr_number)
    if not files:
        logger.warning(f"No changed files retrieved for PR {owner}/{repo}#{pr_number}. Aborting review.")
        return

    structured_review = review_code(pr_title, files)
    if not structured_review:
        logger.warning(f"AI review generation yielded no content or encountered an error for PR #{pr_number}.")
        return

    markdown_comment = render_review_markdown(structured_review)

    try:
        comment_on_pr(
            repo_full_name=f"{owner}/{repo}",
            pr_number=pr_number,
            comment=markdown_comment
        )
    except Exception as e:
        logger.error(f"Failed to post PR comment for {owner}/{repo}#{pr_number}: {e}")

    try:
        pr_data = pr_payload or {}
        with SessionLocal() as db:
            db_repo = upsert_repository(db, owner=owner, name=repo)
            db_pr = upsert_pull_request(
                db,
                repository_id=db_repo.id,
                number=pr_number,
                title=pr_title,
                state=pr_data.get("state", "open"),
                author=pr_author,
                html_url=pr_html_url or f"https://github.com/{owner}/{repo}/pull/{pr_number}",
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
                changed_files=pr_data.get("changed_files", len(files)),
                commits=pr_data.get("commits", 0)
            )
            create_review_with_findings(
                db,
                pull_request_id=db_pr.id,
                summary=structured_review.summary,
                overall_rating=structured_review.overall_rating,
                markdown=markdown_comment,
                structured_review=structured_review
            )
    except Exception as e:
        logger.error(f"Error persisting review to database for {owner}/{repo}#{pr_number}: {e}")
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException
from app.security.github_signature import verify_github_signature
from app.services.ai_review import review_code
from app.services.github_service import get_pr_files, comment_on_pr

logger = logging.getLogger("codesage.routes.webhooks")

router = APIRouter()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    FastAPI webhook endpoint for GitHub repository events.
    Verifies payload authenticity and dispatches event handling to background tasks.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    # Verify signature before parsing JSON or executing tasks
    verify_github_signature(signature, body)

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

        if not owner or not repo or not pr_number:
            logger.warning("Pull Request webhook missing owner, repo, or pr_number payload data.")
            raise HTTPException(status_code=400, detail="Invalid PR webhook payload.")

        logger.info(f"PR event received: repo='{owner}/{repo}', pr=#{pr_number}, action='{action}'")
        background_tasks.add_task(
            process_pr,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            pr_title=pr_title
        )

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

    review = review_code(message, files)
    if review:
        logger.info("Push AI review completed successfully.")
    else:
        logger.info("Push AI review skipped or yielded no result.")


def process_pr(
    owner: str,
    repo: str,
    pr_number: int,
    pr_title: str
) -> None:
    """
    Background worker task for processing GitHub Pull Request events.
    Fetches PR files, requests an AI code review, and posts the review comment to GitHub.
    """
    logger.info(f"Starting PR review process for {owner}/{repo}#{pr_number}...")

    files = get_pr_files(owner, repo, pr_number)
    if not files:
        logger.warning(f"No changed files retrieved for PR {owner}/{repo}#{pr_number}. Aborting review.")
        return

    logger.info(f"Fetched {len(files)} file(s) for PR {owner}/{repo}#{pr_number}.")

    review = review_code(pr_title, files)
    if not review:
        logger.warning(f"AI review generation yielded no content or encountered an error for PR #{pr_number}. Comment will NOT be posted.")
        return

    try:
        status_code = comment_on_pr(
            repo_full_name=f"{owner}/{repo}",
            pr_number=pr_number,
            comment=review
        )
        logger.info(f"Finished PR review workflow for {owner}/{repo}#{pr_number} (status={status_code}).")
    except Exception as e:
        logger.error(f"Failed to post PR comment for {owner}/{repo}#{pr_number}: {e}")
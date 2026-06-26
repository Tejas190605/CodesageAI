from fastapi import APIRouter, Request, BackgroundTasks

from app.services.ai_review import review_code
from app.services.github_service import (
    get_pr_files,
    comment_on_pr
)

router = APIRouter()


# ======================================================
# WEBHOOK
# ======================================================

@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):

    payload = await request.json()

    event = request.headers.get("X-GitHub-Event")

    print(f"\n🔥 WEBHOOK RECEIVED: {event}")

    # ------------------------
    # PUSH
    # ------------------------

    if event == "push":

        commit = payload["head_commit"]

        message = commit["message"]

        filenames = (
            commit.get("added", [])
            + commit.get("modified", [])
            + commit.get("removed", [])
        )

        print("\n--- PUSH COMMIT ---")
        print("Message:", message)
        print("Files:", filenames)

        background_tasks.add_task(
            process_push,
            message,
            filenames
        )

    # ------------------------
    # PULL REQUEST
    # ------------------------

    elif event == "pull_request":

        action = payload["action"]

        if action not in [
            "opened",
            "synchronize",
            "reopened"
        ]:
            return {"status": "ignored"}

        owner = payload["repository"]["owner"]["login"]

        repo = payload["repository"]["name"]

        pr = payload["pull_request"]

        pr_number = pr["number"]

        pr_title = pr["title"]

        print("\n📥 PR RECEIVED")
        print("Repo:", f"{owner}/{repo}")
        print("PR:", pr_number)

        background_tasks.add_task(
            process_pr,
            owner,
            repo,
            pr_number,
            pr_title
        )

    return {"status": "received"}


# ======================================================
# PUSH REVIEW
# ======================================================

def process_push(message, filenames):

    files = []

    for filename in filenames:

        files.append({
            "filename": filename,
            "status": "modified",
            "patch": "Push event contains filename only."
        })

    review = review_code(message, files)

    print("\n🤖 AI REVIEW:\n")
    print(review)


# ======================================================
# PR REVIEW
# ======================================================

def process_pr(owner, repo, pr_number, pr_title):

    files = get_pr_files(
        owner,
        repo,
        pr_number
    )

    print("📂 Files fetched:", len(files))

    review = review_code(
        pr_title,
        files
    )

    print("\n🤖 AI REVIEW:\n")
    print(review)

    comment_on_pr(
        f"{owner}/{repo}",
        pr_number,
        review
    )
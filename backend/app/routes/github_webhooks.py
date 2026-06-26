from fastapi import APIRouter, Request, BackgroundTasks

from app.services.ai_review import review_code
from app.services.github_service import (
    comment_on_pr,
    get_pr_files
)

router = APIRouter()


def process_push(payload):
    print("\n🔥 WEBHOOK RECEIVED: push")

    for commit in payload.get("commits", []):

        message = commit.get("message")

        files = (
            commit.get("modified", [])
            + commit.get("added", [])
            + commit.get("removed", [])
        )

        print("\n--- PUSH COMMIT ---")
        print("Message:", message)
        print("Files:", files)

        ai_review = review_code(message, files)

        print("\n🤖 AI REVIEW:\n")
        print(ai_review)


def process_pr(payload):
    print("\n🔥 WEBHOOK RECEIVED: pull_request")

    action = payload.get("action")

    if action not in ["opened", "synchronize"]:
        return

    repo = payload["repository"]["full_name"]
    pr = payload["pull_request"]
    pr_number = pr["number"]
    title = pr["title"]

    print("\n📥 PR RECEIVED")
    print("Repo:", repo)
    print("PR:", pr_number)

    files = get_pr_files(repo, pr_number)

    ai_review = review_code(title, files)

    print("\n🤖 AI REVIEW:\n")
    print(ai_review)

    comment_on_pr(repo, pr_number, ai_review)


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    payload = await request.json()

    event = request.headers.get("X-GitHub-Event")

    if event == "push":
        background_tasks.add_task(process_push, payload)

    elif event == "pull_request":
        background_tasks.add_task(process_pr, payload)

    return {
        "status": "accepted"
    }
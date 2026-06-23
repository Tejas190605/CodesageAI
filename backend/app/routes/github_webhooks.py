from fastapi import APIRouter, Request

from app.services.ai_review import review_code
from app.services.github_service import (
    comment_on_pr,
    get_pr_files
)

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):

    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    print("\n🔥 WEBHOOK RECEIVED:", event)

    # ======================
    # PUSH EVENT
    # ======================
    if event == "push":

        for commit in payload.get("commits", []):

            message = commit.get("message")

            files = (
                commit.get("modified", [])
                + commit.get("added", [])
            )

            print("\n--- PUSH COMMIT ---")
            print("Message:", message)
            print("Files:", files)

            ai_response = review_code(
                message,
                files
            )

            print("\n🤖 AI REVIEW:\n")
            print(ai_response)

    # ======================
    # PULL REQUEST EVENT
    # ======================
    elif event == "pull_request":

        action = payload.get("action")
        pr = payload.get("pull_request", {})

        if action in ["opened", "synchronize"]:

            repo_name = payload["repository"]["full_name"]
            pr_number = pr["number"]
            pr_title = pr["title"]

            print("\n🔥 PR RECEIVED")
            print("Repo:", repo_name)
            print("PR:", pr_number)

            files = get_pr_files(
                repo_name,
                pr_number
            )

            print(
                f"📂 Files fetched: {len(files)}"
            )

            ai_review = review_code(
                pr_title,
                files
            )

            print("\n🤖 AI REVIEW:\n")
            print(ai_review)

            comment_on_pr(
                repo_name,
                pr_number,
                ai_review
            )

    return {"status": "processed"}
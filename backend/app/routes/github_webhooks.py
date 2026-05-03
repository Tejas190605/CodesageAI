from fastapi import APIRouter, Request
from app.services.ai_review import review_code
from app.services.github_service import comment_on_pr

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    print("\n🔥 WEBHOOK RECEIVED:", event)

    # ======================
    # 🚀 HANDLE PUSH EVENT
    # ======================
    if event == "push":
        for commit in payload.get("commits", []):
            message = commit.get("message")
            files = commit.get("modified", []) + commit.get("added", [])

            print("\n--- PUSH COMMIT ---")
            print("Message:", message)
            print("Files:", files)

            ai_response = review_code(message, files)

            print("\n🤖 AI REVIEW:\n", ai_response)

    # ======================
    # 🚀 HANDLE PR EVENT
    # ======================
    elif event == "pull_request":
        action = payload.get("action")
        pr = payload.get("pull_request", {})

        if action in ["opened", "synchronize"]:

            repo_name = payload.get("repository", {}).get("full_name")
            pr_number = pr.get("number")
            title = pr.get("title")

            print("\n🔥 PR RECEIVED")
            print("Repo:", repo_name)
            print("PR #:", pr_number)

            # 🤖 Generate AI review
            ai_review = review_code(title, [])

            print("\n🤖 AI REVIEW:\n", ai_review)

            # 💬 COMMENT ON PR
            comment_on_pr(repo_name, pr_number, ai_review)

    return {"status": "processed"}
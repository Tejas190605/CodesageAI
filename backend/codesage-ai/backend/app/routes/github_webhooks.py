from fastapi import APIRouter, Request
from app.services.ai_review import review_code
from app.services.github_service import post_pr_comment

router = APIRouter()

@router.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    print("\n" + "="*50)
    print("🔥 WEBHOOK RECEIVED")
    print("Event:", event)

    repo = payload.get("repository", {}).get("full_name")
    print("Repo:", repo)

    print("="*50 + "\n")

    # 🔥 HANDLE PUSH (just print)
    if event == "push":
        for commit in payload.get("commits", []):
            message = commit.get("message")
            files = commit.get("modified", []) + commit.get("added", [])

            print("\n--- PUSH COMMIT ---")
            print("Message:", message)
            print("Files:", files)

            # 🤖 AI REVIEW
            ai_response = review_code(message, files)

            print("\n🤖 AI REVIEW:\n", ai_response)

    # 🔥 HANDLE PULL REQUEST (MAIN FEATURE)
    elif event == "pull_request":

        action = payload.get("action")
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number")

        print("\n--- PULL REQUEST ---")
        print("Action:", action)
        print("PR Number:", pr_number)

        # Only run on opened / synchronize
        if action in ["opened", "synchronize"]:

            title = pr.get("title")
            body = pr.get("body") or ""

            # 🤖 AI REVIEW
            ai_response = review_code(title + "\n" + body, [])

            print("\n🤖 AI REVIEW:\n", ai_response)

            # 🚀 POST COMMENT TO GITHUB
            post_pr_comment(
                repo=repo,
                pr_number=pr_number,
                comment=ai_response
            )

    return {"status": "received"}
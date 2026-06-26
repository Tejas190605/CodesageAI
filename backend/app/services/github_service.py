import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


# ======================================================
# GET PR FILES
# ======================================================

def get_pr_files(owner, repo, pr_number):

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30
    )

    print("📂 Fetch PR Files:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return []

    github_files = response.json()

    files = []

    for file in github_files:

        files.append({
            "filename": file.get("filename", ""),
            "status": file.get("status", ""),
            "patch": file.get("patch", "No patch available")
        })

    return files


# ======================================================
# COMMENT ON PR
# ======================================================

def comment_on_pr(repo_full_name, pr_number, comment):

    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"

    response = requests.post(
        url,
        headers=get_headers(),
        json={
            "body": comment
        },
        timeout=30
    )

    print("✅ GitHub Comment Status:", response.status_code)

    if response.status_code != 201:
        print(response.text)

    return response.status_code
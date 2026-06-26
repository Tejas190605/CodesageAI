import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def get_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


def comment_on_pr(repo_full_name, pr_number, comment):

    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"

    response = requests.post(
        url,
        headers=get_headers(),
        json={
            "body": comment
        }
    )

    print("✅ GitHub Comment Status:", response.status_code)

    if response.status_code != 201:
        print(response.text)


def get_pr_files(owner, repo, pr_number):
    """
    Returns the ACTUAL code changes (diffs)
    instead of only filenames.
    """

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"

    response = requests.get(url, headers=headers)

    print("📂 Fetch PR Files:", response.status_code)

    if response.status_code != 200:
        return []

    files = response.json()

    review_data = []

    for file in files:

        review_data.append({
            "filename": file.get("filename"),
            "status": file.get("status"),
            "patch": file.get("patch", "No patch available")
        })

    return review_data
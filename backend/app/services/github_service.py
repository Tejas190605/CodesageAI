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


def comment_on_pr(
    repo_full_name,
    pr_number,
    comment
):

    url = (
        f"https://api.github.com/repos/"
        f"{repo_full_name}/issues/"
        f"{pr_number}/comments"
    )

    response = requests.post(
        url,
        headers=get_headers(),
        json={"body": comment}
    )

    print(
        "✅ GitHub Comment Status:",
        response.status_code
    )


def get_pr_files(
    repo_full_name,
    pr_number
):

    url = (
        f"https://api.github.com/repos/"
        f"{repo_full_name}/pulls/"
        f"{pr_number}/files"
    )

    response = requests.get(
        url,
        headers=get_headers()
    )

    print(
        "📂 Fetch PR Files:",
        response.status_code
    )

    if response.status_code != 200:
        print(response.text)
        return []

    return response.json()
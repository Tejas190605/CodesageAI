import requests
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def post_pr_comment(repo, pr_number, comment):
    """
    repo = owner/repo
    pr_number = pull request number
    comment = AI text
    """

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "body": comment
    }

    response = requests.post(url, headers=headers, json=data)

    print("📤 GitHub Comment Status:", response.status_code)
    print("Response:", response.text)
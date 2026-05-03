import requests
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def comment_on_pr(repo_full_name, pr_number, comment):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "body": comment
    }

    response = requests.post(url, headers=headers, json=data)

    print("✅ GitHub Comment Status:", response.status_code)
    print(response.text)
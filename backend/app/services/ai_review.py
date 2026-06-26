import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("GEMINI KEY LOADED:", api_key is not None)

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found.")

client = genai.Client(api_key=api_key)


def review_code(commit_message, files):

    try:

        code_changes = ""

        for file in files:

            code_changes += f"""

==========================
FILE: {file['filename']}
STATUS: {file['status']}
==========================

{file['patch']}

"""

        prompt = f"""
You are a Senior Software Engineer.

Review the following GitHub Pull Request.

Commit Message:
{commit_message}

Code Changes:

{code_changes}

Review in this exact format.

## Security Issues

## Bug Risks

## Code Quality

## Performance Concerns

## Best Practice Suggestions

## Overall Rating (/10)

Only review the ACTUAL code changes.

Do not mention that the diff is missing.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"AI Error: {e}"
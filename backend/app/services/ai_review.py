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

    prompt = f"""
You are a Senior Software Engineer performing a GitHub code review.

Review the following code changes.

Commit / PR Title:
{commit_message}

Changed Files:
{files}

Provide:

## Security Issues
## Bug Risks
## Code Quality
## Performance Concerns
## Best Practice Suggestions
## Overall Rating (/10)

Be specific and practical.
"""

    max_retries = 3

    for attempt in range(max_retries):

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return response.text

        except Exception as e:

            error_text = str(e)

            print(f"⚠ Gemini Attempt {attempt + 1} Failed:")
            print(error_text)

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"🔄 Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return f"❌ AI Error: {error_text}"
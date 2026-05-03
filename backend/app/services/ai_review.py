import os
from dotenv import load_dotenv
from google import genai

# Load env
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

print("GEMINI KEY LOADED:", api_key is not None)

if not api_key:
    raise ValueError("❌ GOOGLE_API_KEY not found. Check .env file.")

# Create client
client = genai.Client(api_key=api_key)


def review_code(commit_message, files):
    try:
        prompt = f"""
You are a senior software engineer.

Review this GitHub change:

Commit Message:
{commit_message}

Files Changed:
{files}

Give:
1. Issues
2. Improvements
3. Suggestions
4. Rating out of 10
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"❌ AI Error: {str(e)}"
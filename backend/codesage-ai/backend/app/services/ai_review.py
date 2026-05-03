import os
from dotenv import load_dotenv
from google import genai

# ✅ Load .env
load_dotenv()

# ✅ Get API key
api_key = os.getenv("GEMINI_API_KEY")
print("GEMINI KEY LOADED:", api_key is not None)

# ✅ Create Gemini client
client = genai.Client(api_key=api_key)


def review_code(commit_message, files):
    try:
        prompt = f"""
You are a senior software engineer.

Review this GitHub commit:

Commit Message:
{commit_message}

Files Changed:
{files}

Give:
- Issues
- Improvements
- Suggestions
- Rating out of 10
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",  # ✅ correct model
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"AI ERROR: {str(e)}"
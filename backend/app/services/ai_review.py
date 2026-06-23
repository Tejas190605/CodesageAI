import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("GEMINI KEY LOADED:", api_key is not None)

if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found")

client = genai.Client(api_key=api_key)


def review_code(title, files):

    try:

        file_text = ""

        for file in files:

            filename = file.get("filename", "unknown")

            patch = file.get("patch", "")

            file_text += f"""

FILE: {filename}

CODE CHANGES:

{patch}

=================================
"""

        prompt = f"""
You are a Senior Software Engineer.

Review this Pull Request.

TITLE:
{title}

FILES:

{file_text}

Give:

## Issues

## Improvements

## Suggestions

## Security Concerns

## Rating /10

Keep review professional.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"❌ AI Error: {str(e)}"
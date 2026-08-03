# CodeSage AI

AI-powered GitHub Pull Request code reviewer built with FastAPI, GitHub Webhooks and Google Gemini.

## Current Features

* **GitHub Webhook Integration**: Listens for GitHub `push` and `pull_request` webhook events via FastAPI.
* **Webhook Signature Verification**: Verifies incoming GitHub payload authenticity using HMAC-SHA256 and `X-Hub-Signature-256`.
* **Asynchronous Processing**: Uses FastAPI `BackgroundTasks` to quickly acknowledge webhooks (HTTP 200) and prevent GitHub timeouts.
* **PR File & Diff Retrieval**: Queries GitHub REST API to fetch modified files and line-by-line patch diffs.
* **AI Code Review Generation**: Uses `google-genai` SDK (`gemini-2.5-flash`) to generate structured code reviews (Security, Bug Risks, Code Quality, Performance, Best Practices, Overall Rating).
* **Automated PR Commenting**: Posts generated AI reviews directly to the GitHub PR discussion thread.

## Architecture

```
GitHub Webhook  -->  FastAPI Endpoint (/webhook)  -->  Signature Verification
                                                            |
                                                            v (Background Task)
GitHub PR Comments  <--  Gemini 2.5 Flash Review  <--  Fetch PR Patch Diffs (GitHub REST API)
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entrypoint
│   ├── routes/
│   │   └── github_webhooks.py  # Webhook route handler & background processor
│   ├── security/
│   │   └── github_signature.py # HMAC SHA-256 signature verification
│   └── services/
│       ├── ai_review.py        # Gemini AI prompt formatting & API integration
│       └── github_service.py   # GitHub REST API client (files & comments)
├── .env                        # Local environment secrets (untracked)
├── .gitignore                  # Git ignore patterns
└── requirements.txt            # Python dependencies
```

## Requirements

* Python 3.10+ (Tested on Python 3.14)
* Google Gemini API Key
* GitHub Personal Access Token (Repo scope)
* GitHub Webhook Secret

## Environment Variables

Configure the following environment variable names in your `.env` file:

* `GEMINI_API_KEY`: API key for Google Gemini model access.
* `GITHUB_TOKEN`: GitHub Personal Access Token with repository comment permissions.
* `GITHUB_WEBHOOK_SECRET`: Shared secret configured in GitHub repository Webhook settings.

> **Note**: Never commit `.env` or expose secret values.

## Local Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in `backend/` with your credentials.

## Running the Server

Start the Uvicorn development server:

```bash
uvicorn app.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`.

## GitHub Webhook Setup

1. Expose your local port via ngrok or similar tunneling service:
   ```bash
   ngrok http 8000
   ```
2. In your GitHub Repository Settings $\rightarrow$ Webhooks $\rightarrow$ Add Webhook:
   * **Payload URL**: `https://<your-ngrok-domain>/webhook`
   * **Content type**: `application/json`
   * **Secret**: `<Your GITHUB_WEBHOOK_SECRET>`
   * **Events**: Select `Pull requests` and `Pushes`.

## Current Limitations

* **No Gemini Retries**: Lacks automatic exponential backoff for Gemini 429/503 errors.
* **Single-Page File Fetching**: Does not paginate PR file results (>30 files per PR).
* **Basic Token Budgeting**: No diff chunking or truncation for very large PRs.
* **Push Event Patch Content**: Push webhooks process filenames without fetching full commit diffs.
* **Lack of Filtering**: Generated lockfiles and binary files are not excluded from reviews.

## Planned Improvements

* Add exponential backoff retry handling for Gemini API requests.
* Add pagination for GitHub PR file retrieval.
* Add lockfile, binary, and minified file filtering.
* Implement diff size limits and prompt chunking.
* Add structured logging and comprehensive pytest test suite.

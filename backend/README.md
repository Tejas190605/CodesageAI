# CodeSage AI

AI-powered GitHub Pull Request code reviewer built with FastAPI, GitHub Webhooks and Google Gemini.

## Current Features

* **GitHub Webhook Integration**: Listens for GitHub `push` and `pull_request` webhook events via FastAPI.
* **Webhook Signature Verification**: Verifies incoming GitHub payload authenticity using HMAC-SHA256 and `X-Hub-Signature-256`.
* **Asynchronous Processing**: Uses FastAPI `BackgroundTasks` to quickly acknowledge webhooks (HTTP 200) and prevent GitHub timeouts.
* **GitHub PR File Pagination**: Fetches up to 1,000 modified files per PR across multiple pages (`per_page=100`).
* **Non-Reviewable File Filtering**: Automatically excludes lockfiles, minified code, binary/image files, and vendor/build directories from AI prompts.
* **Diff Truncation & Token Budgeting**: Caps file patch sizes (`12,000` chars/file) and overall diff size (`60,000` chars total) to prevent LLM context overflows.
* **Structured AI Review Engine**: Generates strongly-typed Pydantic `StructuredReview` models directly from Gemini via `response_schema` JSON mode.
* **Dual Markdown & JSON Pipeline**: Internally structures reviews into typed findings (`security`, `bug_risk`, `code_quality`, `performance`, `best_practice`) and renders clean GitHub Markdown comments.
* **Transient Error Retry Policy**: Bounded exponential backoff retries via `tenacity` for transient Gemini API errors (429/503) and GitHub REST API drops.
* **Automated PR Commenting**: Posts generated AI reviews directly to the GitHub PR discussion thread.
* **Health Monitoring Endpoint**: Includes `GET /health` for service health checks.

## Architecture

```
GitHub PR Webhook
       ↓
Signature Verification (HMAC-SHA256)
       ↓
Fetch / Filter / Truncate Diff (GitHub REST API)
       ↓
Gemini 2.5 Flash (Structured Output JSON Mode via response_schema)
       ↓
StructuredReview (Pydantic Model)
       ├── Future REST API / Frontend Consumption
       └── Markdown Renderer (render_review_markdown)
                ↓
           GitHub PR Comment Thread
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entrypoint & health routes
│   ├── config.py               # Centralized Pydantic settings
│   ├── models/
│   │   └── review.py           # StructuredReview & ReviewFinding Pydantic models
│   ├── routes/
│   │   └── github_webhooks.py  # Webhook route handler & background processor
│   ├── security/
│   │   └── github_signature.py # HMAC SHA-256 signature verification
│   ├── services/
│   │   ├── ai_review.py        # Gemini AI structured review engine
│   │   ├── github_service.py   # GitHub REST API client (paginated files & comments)
│   │   └── review_renderer.py  # Markdown renderer converting StructuredReview -> Markdown
│   └── utils/
│       └── diff_utils.py       # File filtering & diff truncation logic
├── tests/                      # Pytest automated test suite
├── .env                        # Local environment secrets (untracked)
├── .gitignore                  # Git ignore patterns
├── requirements.txt            # Production Python dependencies
└── requirements-dev.txt        # Development & testing dependencies
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

## Testing

The backend includes a comprehensive automated pytest test suite covering API routes, signature verification, REST API pagination and retries, file filtering, diff truncation, Pydantic models, markdown renderer, and prompt safety.

To run the tests:

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run pytest:
   ```bash
   python -m pytest -v
   ```

> **Note**: All external API calls (GitHub REST API and Google Gemini API) are completely mocked during testing and do not perform network requests or require live API credentials.

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

## Planned Improvements

* Add persistent background task queue (Redis + worker process) to prevent task loss on server restart.
* Build frontend web interface for repository settings, analytics, and historical PR reviews.
* Add multi-repository support and user authentication.

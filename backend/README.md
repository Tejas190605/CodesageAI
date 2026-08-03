# CodeSage AI

AI-powered GitHub Pull Request code reviewer built with FastAPI, GitHub Webhooks, and Google Gemini.

## Current Features

* **GitHub Webhook Integration**: Listens for GitHub `push` and `pull_request` webhook events via FastAPI.
* **Webhook Signature Verification**: Verifies incoming GitHub payload authenticity using HMAC-SHA256 and `X-Hub-Signature-256`.
* **Asynchronous Processing**: Uses FastAPI `BackgroundTasks` to quickly acknowledge webhooks (HTTP 200) and prevent GitHub timeouts.
* **GitHub PR File Pagination**: Fetches up to 1,000 modified files per PR across multiple pages (`per_page=100`).
* **Non-Reviewable File Filtering**: Automatically excludes lockfiles, minified code, binary/image files, and vendor/build directories from AI prompts.
* **Diff Truncation & Token Budgeting**: Caps file patch sizes (`12,000` chars/file) and overall diff size (`60,000` chars total) to prevent LLM context overflows.
* **Structured AI Review Engine**: Generates strongly-typed Pydantic `StructuredReview` models directly from Gemini via `response_schema` JSON mode.
* **Dual Markdown & JSON Pipeline**: Internally structures reviews into typed findings (`security`, `bug_risk`, `code_quality`, `performance`, `best_practice`) and renders clean GitHub Markdown comments.
* **Dashboard & Read APIs**: Serves clean, typed REST APIs for monitored repositories, PR metadata, review history, and dashboard aggregation.
* **CORS Support**: Configurable CORS middleware (`CORS_ORIGINS`) allowing seamless Next.js frontend integration.
* **Transient Error Retry Policy**: Bounded exponential backoff retries via `tenacity` for transient Gemini API errors (429/503) and GitHub REST API drops.
* **Automated PR Commenting**: Posts generated AI reviews directly to the GitHub PR discussion thread.
* **Health Monitoring Endpoint**: Includes `GET /health` for service health checks.

## Architecture

```
GitHub PR Webhook  -->  Signature Verification (HMAC-SHA256)
                              │
                              ▼ (Background Worker Task)
                    Fetch / Filter / Truncate Diff (GitHub REST API)
                              │
                              ▼
                    Gemini 2.5 Flash (Structured JSON Output)
                              │
                              ▼
                    StructuredReview (Pydantic Model)
                        ├── Markdown Renderer  -->  GitHub PR Discussion Comment
                        └── Dashboard REST APIs <--  GitHub API Aggregation Engine
```

### MVP Data Strategy & Limitations

CodeSage AI uses the **GitHub REST API as the primary authoritative data source for MVP dashboard aggregation**.
* No external database (e.g. PostgreSQL) is required for the MVP.
* Historical PR review metadata is parsed dynamically from CodeSage review comments (`# CodeSage AI Review`) on GitHub PR threads.
* Full persistent historical findings analytics will be added in Phase 4.

## Backend REST API Endpoints

* `GET /health`: Service health status.
* `GET /api/dashboard`: Aggregated statistics across monitored repositories.
* `GET /api/repositories`: List configured monitored repositories with live GitHub metadata.
* `GET /api/repositories/{owner}/{repo}`: Detailed repository metadata and pull request list.
* `GET /api/repositories/{owner}/{repo}/pulls`: Filtered pull request list (`state=open|closed|all`).
* `GET /api/pulls/{owner}/{repo}/{number}`: Detailed metadata for a single pull request.
* `GET /api/pulls/{owner}/{repo}/{number}/review`: Latest CodeSage review details and history for a pull request.

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entrypoint, CORS, & routers
│   ├── config.py               # Centralized Pydantic settings & repo parsing
│   ├── models/
│   │   ├── review.py           # StructuredReview & ReviewFinding Pydantic models
│   │   └── github.py           # Dashboard & GitHub API response Pydantic schemas
│   ├── routes/
│   │   ├── github_webhooks.py  # Webhook route handler & background processor
│   │   └── api.py              # Dashboard & repository REST API routes
│   ├── security/
│   │   └── github_signature.py # HMAC SHA-256 signature verification
│   ├── services/
│   │   ├── ai_review.py        # Gemini AI structured review engine
│   │   ├── github_service.py   # GitHub REST API client (files, repos, PRs, comments)
│   │   └── review_renderer.py  # Markdown renderer & score extractor
│   └── utils/
│       └── diff_utils.py       # File filtering & diff truncation logic
├── tests/                      # Pytest automated test suite
├── .env                        # Local environment secrets (untracked)
├── .gitignore                  # Git ignore patterns
├── requirements.txt            # Production Python dependencies
└── requirements-dev.txt        # Development & testing dependencies
```

## Environment Variables

Configure the following environment variable names in your `.env` file:

* `GEMINI_API_KEY`: API key for Google Gemini model access.
* `GITHUB_TOKEN`: GitHub Personal Access Token with repository comment permissions.
* `GITHUB_WEBHOOK_SECRET`: Shared secret configured in GitHub repository Webhook settings.
* `CODESAGE_REPOSITORIES`: Comma-separated list of monitored repositories e.g. `owner/repo1,owner/repo2`.
* `CORS_ORIGINS`: Comma-separated list of allowed CORS origins (default: `http://localhost:3000`).

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

4. Create a `.env` file in `backend/` with your credentials and monitored repositories.

## Running the Server

Start the Uvicorn development server:

```bash
uvicorn app.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

## Testing

The backend includes a comprehensive automated pytest test suite covering API routes, signature verification, REST API pagination, file filtering, diff truncation, Pydantic models, markdown renderer, score extraction, dashboard aggregation, and prompt safety.

To run the tests:

```bash
python -m pytest -v
```

> **Note**: All external API calls (GitHub REST API and Google Gemini API) are completely mocked during testing and do not perform network requests or require live API credentials.

## Planned Improvements

* Build Next.js 14 frontend web interface for repository settings, analytics, and historical PR reviews.
* Add persistent background task queue (Redis + worker process).
* Add multi-repository PostgreSQL database persistence and user authentication.

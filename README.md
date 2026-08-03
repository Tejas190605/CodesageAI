# CodeSage AI — AI Developer Assistant & Automated GitHub Code Review Platform

CodeSage AI is an intelligent automated code review engine and developer dashboard. It seamlessly connects to GitHub repositories via Webhooks, fetches Pull Request diffs, performs structured multi-dimensional code analysis using Google Gemini AI, posts formatted reviews directly to PR discussion threads, and presents a modern Next.js developer dashboard for monitoring repository health and code quality metrics.

---

## Architecture Overview

```text
  GitHub Repository (Pull Request / Push Event)
         │
         ▼ (HMAC-SHA256 Signed Webhook)
  FastAPI Backend (http://127.0.0.1:8000)
    ├── HMAC Signature Verification (app/security/github_signature.py)
    ├── Webhook Idempotency Delivery Tracker (app/services/delivery_tracker.py)
    ├── GitHub File Fetching & Diff Truncation (app/services/github_service.py)
    ├── Gemini 2.5 Structured Review Engine (app/services/ai_review.py)
    └── Markdown Renderer & PR Commenter (app/services/review_renderer.py)
         │
         ▼ (REST APIs)
  Next.js 16 Developer Dashboard (http://localhost:3000)
    ├── Dashboard Overview (/)
    ├── Monitored Repositories (/repos)
    ├── Repository Detail & PR Filter (/repos/[owner]/[repo])
    ├── AI Review & Findings Detail (/repos/[owner]/[repo]/pulls/[number])
    └── Integration & Webhook Settings (/settings)
```

---

## Core Features

* **Automated Webhook Code Reviews**: Instant analysis on PR events (`opened`, `synchronize`, `reopened`).
* **Structured AI Engine**: Powered by Gemini 2.5 Flash with Pydantic JSON schema enforcement (`StructuredReview`), scoring overall code quality ($1-10$) across 6 distinct dimensions:
  1. Summary & Architecture Overview
  2. Security Vulnerabilities (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`)
  3. Bug Risks & Logic Flaws
  4. Code Quality & Readability
  5. Performance Concerns
  6. Best Practice & Style Suggestions
* **Webhook Delivery Idempotency**: LRU `X-GitHub-Delivery` tracker prevents duplicate AI runs on redelivered webhooks.
* **Resilient Retry Policy**: `tenacity` exponential backoff retries for transient Gemini / GitHub API network errors.
* **Diff Truncation Budgeting**: Per-file and global token budgeting prevents payload context window overflow.
* **Modern Developer Dashboard**: Next.js 16 App Router UI with real-time backend connection status, dark mode tokens, interactive PR filters, and safe Markdown rendering.

---

## Technology Stack

* **Backend**: Python 3.14+, FastAPI, Uvicorn, Pydantic v2, `google-genai` SDK, `httpx`, `tenacity`, `pytest`
* **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, `lucide-react`
* **Integrations**: GitHub REST APIs, GitHub Webhooks (HMAC-SHA256), Google Gemini 2.5 Flash

---

## Repository Structure

```text
codesage-ai/
├── backend/                                # FastAPI Backend Engine
│   ├── app/
│   │   ├── main.py                         # FastAPI Application Entrypoint & CORS Config
│   │   ├── config.py                       # Pydantic Settings & Environment Parsing
│   │   ├── models/                         # Review Schemas & Pydantic Data Models
│   │   ├── routes/                         # Webhook & REST API Routes
│   │   ├── security/                       # HMAC Signature Verification
│   │   ├── services/                       # Gemini AI, GitHub Service, Delivery Tracker
│   │   └── utils/                          # Diff Filtering & Budgeting Utilities
│   ├── tests/                              # 74 Pytest Unit & Integration Tests
│   ├── requirements.txt                    # Production Dependencies
│   └── .env.example                        # Backend Environment Template
├── frontend/                               # Next.js 16 Developer Dashboard
│   ├── src/
│   │   ├── app/                            # App Router Routes (/, /repos, /settings)
│   │   ├── components/                     # Layout & UI Components
│   │   └── lib/                            # API Client & TypeScript Types
│   ├── package.json                        # Frontend Dependencies
│   ├── .env.local.example                  # Frontend Environment Template
│   └── README.md                           # Frontend Component Documentation
├── .github/workflows/                      # GitHub Actions CI Workflows
│   ├── backend-tests.yml                   # Automated Backend Pytest CI Workflow
│   └── frontend-tests.yml                  # Automated Frontend Next.js Lint & Build CI
└── README.md                               # Root Monorepo Documentation
```

---

## Environment Variables

### Backend Configuration (`backend/.env`)

```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here
CODESAGE_REPOSITORIES=Tejas190605/codexproj
CORS_ORIGINS=http://localhost:3000
```

> **Security Note**: Never commit `backend/.env` or expose API tokens in source repositories.

### Frontend Configuration (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

---

## Local Development & Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Backend will start at `http://127.0.0.1:8000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will start at `http://localhost:3000`.

---

## Running Automated Tests

### Backend Test Suite (74 Tests)

```bash
cd backend
python -m pytest -v
python -m compileall app
```

### Frontend Quality & Build Verification

```bash
cd frontend
npm run lint
npm run build
```

---

## Development Workflow

To contribute or add new features to CodeSage AI:

1. Start from an up-to-date `main` branch: `git checkout main && git pull origin main`
2. Create a focused feature branch: `git checkout -b feature/my-feature`
3. Implement changes and verify locally with automated tests (`pytest`, `npm run lint`, `npm run build`).
4. Commit focused code changes with clear commit messages.
5. Push your feature branch normally: `git push -u origin feature/my-feature`
6. Open a Pull Request targeting `main`. Both Backend CI and Frontend CI must pass before merging.

---

## GitHub Webhook Integration Setup

1. Start an ngrok tunnel pointing to port 8000:
   ```bash
   ngrok http 8000
   ```
2. Navigate to your GitHub Repository $\rightarrow$ **Settings** $\rightarrow$ **Webhooks** $\rightarrow$ **Add webhook**.
3. **Payload URL**: `https://<your-ngrok-subdomain>.ngrok-free.app/webhook`
4. **Content type**: `application/json`
5. **Secret**: Enter the exact secret string defined in `GITHUB_WEBHOOK_SECRET`.
6. **Events**: Select **Pushes** and **Pull requests**.
7. Save the webhook. CodeSage AI will now automatically analyze and review PRs on creation or push updates!

---

## Security Guidelines

* Secret keys (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`) are restricted strictly to the FastAPI backend environment.
* The Next.js frontend communicates exclusively with FastAPI endpoints. Zero direct browser requests are made to external GitHub APIs.
* Webhook requests are cryptographically verified using `HMAC-SHA256` timing-safe comparisons (`hmac.compare_digest`).

---

## Phase Roadmap

* [x] **Phase 1**: Backend Repository Cleanup & Normalization
* [x] **Phase 2**: Backend Hardening, Retries, Diff Limits, Webhook Security, & Pytest Suite
* [x] **Phase 3A-3E**: Structured Gemini AI Review Engine, Dashboard REST APIs, & Next.js 16 Frontend MVP
* [x] **Phase 3F**: Webhook Idempotency Tracker, End-to-End Verification, & MVP Local Release Checkpoint
* [x] **Phase 3G-3J**: Unified Monorepo Migration, Controlled Main Branch Alignment, & Dual Monorepo CI
* [x] **Phase 3K**: Post-Migration Stabilization & Standard Development Workflow Validation
* [ ] **Phase 4**: PostgreSQL Persistence, Redis Worker Queues, GitHub App OAuth Auth, & Production Deployment

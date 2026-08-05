# CodeSage AI — Enterprise AI-Powered Code Review & Repository Intelligence Platform

> **CodeSage AI** is a production-grade, multi-tenant developer assistant platform that automates GitHub Pull Request code reviews using Google Gemini 2.5 Flash and multi-LLM orchestration, performs semantic codebase RAG retrieval, enforces custom security policies, tracks audit events, and delivers engineering analytics via a modern Next.js 16 dashboard.

---

## Overview

Modern software teams spend hundreds of hours reviewing Pull Requests, looking for security flaws, credential leaks, performance regressions, and style violations. **CodeSage AI** automates PR code reviews by combining:
1. **GitHub App & Webhook Event Processing**: Immediate, secure delivery handling with HMAC SHA-256 verification and LRU idempotency deduplication.
2. **Semantic Codebase RAG Intelligence**: Language-aware AST/regex chunking and Reciprocal Rank Fusion (RRF) hybrid code search to give the AI engine deep cross-file repository context.
3. **Security Policy Engine**: Deterministic rules detecting hardcoded secrets, leftover debug statements, dependency manifest changes, and missing test files before LLM invocation.
4. **Multi-LLM Provider Registry**: Flexible model dispatching supporting Google Gemini, OpenAI, and Anthropic with automatic failover and token cost tracking.
5. **Engineering Analytics & Audit Trail**: Real-time review metrics, finding severity breakdowns, AI token expenses, job queue health, and sanitized immutable audit logs.

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph GitHub ["GitHub Infrastructure"]
        GHApp["GitHub App / Webhook"]
        GHPR["Pull Request Thread"]
    end

    subgraph Platform ["CodeSage AI Monorepo Engine"]
        FastAPI["FastAPI Backend (app/main.py)"]
        DeliveryTracker["Delivery Tracker & HMAC Security"]
        Postgres[(PostgreSQL 15 + pgvector)]
        RedisQueue[("Redis Queue / ARQ Worker")]
        Worker["Async Worker Loop (app/worker.py)"]
        Chunker["AST/Regex Code Chunker"]
        RAGEngine["Hybrid RRF Semantic Search"]
        PolicyEngine["Security Policy Engine"]
        LLMRegistry["Multi-LLM Provider Registry"]
        Publisher["GitHub Review Publisher"]
    end

    subgraph Frontend ["Next.js 16 Web Dashboard"]
        NextJS["Next.js App Router (http://localhost:3000)"]
    end

    GHApp -->|HMAC Webhook| FastAPI
    FastAPI --> DeliveryTracker
    DeliveryTracker -->|Enqueue ReviewJob| RedisQueue
    RedisQueue --> Worker
    Worker -->|Fetch PR Files & Diff| GHApp
    Worker -->|Query Code Chunks| RAGEngine
    RAGEngine -->|Semantic Context| Chunker
    Chunker <--> Postgres
    Worker --> PolicyEngine
    PolicyEngine -->|Deterministic Rules| LLMRegistry
    LLMRegistry -->|Structured AI Review| Publisher
    Publisher -->|Post Markdown & Inline Comments| GHPR
    Worker -->|Persist Review & Audit Event| Postgres
    NextJS <-->|REST APIs| FastAPI
```

---

## Key Features

- **Automated AI PR Reviews**: Actionable PR reviews with overall quality scores ($1-10$), line-level suggestions, and severity decision logic (`APPROVE`, `COMMENT`, `REQUEST_CHANGES`).
- **Repository Intelligence & RAG**: Codebase indexing using AST/regex chunkers across Python, JS/TS/TSX, Java, and Go, coupled with pgvector/hybrid RRF search to feed relevant context into review prompts.
- **Security Policy Engine**: `.codesage.yml` safe parsing with precedence hierarchy (Repo Config $\rightarrow$ Org Overrides $\rightarrow$ System Defaults) and deterministic rules for secrets, debug code, dependencies, and test coverage.
- **Secret Redaction & Audit Safety**: Automated SHA-256 fingerprint finding deduplication and recursive scrubbing of sensitive keys (`token`, `secret`, `api_key`, `password`, `authorization`).
- **Multi-LLM Provider Registry**: Abstracted LLM driver interface with runtime provider selection, fallback handling, prompt versioning, and token cost tracking.
- **Enterprise Engineering Analytics**: Real-time overview metrics, finding severities, review velocity, AI costs/tokens, and job queue success rates.
- **Production Infrastructure**: Fully containerized (`Docker`, `docker-compose.prod.yml`), Kubernetes deployment manifests (`k8s/`), and automated GitHub Actions CI/CD workflows.

---

## Application Modules & Screenshots

| Module | Route | Description |
| :--- | :--- | :--- |
| **Dashboard** | `/` | Executive overview of monitored repositories, active pull requests, and review metrics. |
| **Repositories** | `/repos` | Monitored repository list, indexing status, and pull request activity streams. |
| **Code Search** | `/search` | Semantic hybrid RRF codebase search with file citations and code snippet previews. |
| **Policies** | `/policies` | Interactive policy management for custom review rules and severity thresholds. |
| **Analytics** | `/analytics` | Engineering metrics for review turnaround, finding severities, AI token costs, and job queue health. |
| **Audit Log** | `/audit-log` | Immutable, sanitized security trail for user authentication, indexing, and review operations. |
| **Job Queue** | `/jobs` | Worker background job queue monitoring, retry counts, and worker health status. |
| **AI Platform** | `/ai-settings` | Multi-LLM provider registry status, active prompt templates, and evaluation runs. |
| **Installations** | `/installations` | GitHub App organization installations, repository permissions, and account binding. |
| **Profile** | `/profile` | Authenticated user profile, GitHub OAuth session status, and organization memberships. |

---

## Technology Stack

- **Backend**: Python 3.14+, FastAPI, Uvicorn, Gunicorn, SQLAlchemy 2.0, Alembic, PostgreSQL + pgvector, Redis + ARQ, PyJWT, PyYAML, `google-genai` SDK, `pytest`
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, `lucide-react`
- **Infrastructure**: Docker, Docker Compose, Kubernetes, GitHub Actions CI/CD, Prometheus Metrics
- **Integrations**: GitHub REST APIs, GitHub App OAuth 2.0, GitHub Webhooks (HMAC SHA-256), Google Gemini 2.5 Flash

---

## Repository Structure

```text
codesage-ai/
├── backend/                                # FastAPI Backend Engine
│   ├── alembic/                            # Alembic Database Migrations (001 -> 007)
│   ├── app/
│   │   ├── main.py                         # FastAPI App Entrypoint & Router Registry
│   │   ├── config.py                       # Pydantic Settings & Environment Parsing
│   │   ├── database.py                     # SQLAlchemy 2.0 Session & Engine Setup
│   │   ├── models/                         # Database ORM & Pydantic Review Models
│   │   ├── routes/                         # REST API Routers (Auth, Repos, Search, Policies, Analytics, Audit)
│   │   ├── security/                       # HMAC Webhook Verification & JWT Auth
│   │   ├── services/                       # RAG, Policy Engine, LLM Registry, Audit, Analytics, Worker
│   │   └── worker.py                       # Async Worker Review Pipeline Execution
│   ├── tests/                              # 142 Pytest Unit & Integration Tests
│   ├── Dockerfile                          # Backend Container Image Definition
│   └── requirements.txt                    # Production Python Dependencies
├── frontend/                               # Next.js 16 Developer Dashboard
│   ├── src/
│   │   ├── app/                            # 15 App Router Routes (/, /repos, /search, /policies, /analytics, /audit-log)
│   │   ├── components/                     # Layout, Sidebar, & UI Components
│   │   └── lib/                            # API Client Library & TypeScript Interfaces
│   └── Dockerfile                          # Frontend Container Image Definition
├── k8s/                                    # Production Kubernetes Deployment Manifests
├── docs/                                   # Architectural & Deployment Documentation
│   ├── ARCHITECTURE.md                     # Deep Dive System Architecture
│   ├── LOCAL_DEVELOPMENT.md                # PowerShell & Docker Development Guide
│   ├── DEPLOYMENT_GUIDE.md                 # Production Docker & K8s Deployment Guide
│   ├── API.md                              # REST API Reference Documentation
│   ├── RELEASE_NOTES_v1.0.md               # CodeSage AI v1.0 Feature Release Summary
│   └── RELEASE_CHECKLIST.md                # Pre-Flight Deployment Checklist
├── .github/workflows/                      # GitHub Actions Automated CI/CD Pipelines
├── docker-compose.yml                      # Development Multi-Container Compose Setup
├── docker-compose.prod.yml                 # Production Stack Definition
├── SECURITY.md                             # Vulnerability Reporting & Security Policies
└── README.md                               # Project Overview & Quickstart Guide
```

---

## Quickstart & Local Development

### 1. Backend Setup (Windows PowerShell)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Backend REST APIs will start at `http://127.0.0.1:8000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend Dashboard will start at `http://localhost:3000`.

---

## Environment Variables

Copy template environment files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

### Key Environment Variables Matrix

| Variable | Scope | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | Backend | PostgreSQL connection string (`postgresql://user:pass@host:5432/db`) |
| `REDIS_URL` | Backend | Redis queue connection string (`redis://localhost:6379/0`) |
| `GEMINI_API_KEY` | Backend | Google Gemini AI API key |
| `GITHUB_WEBHOOK_SECRET` | Backend | HMAC SHA-256 Webhook signature secret key |
| `GITHUB_APP_ID` | Backend | GitHub App ID for authentication |
| `GITHUB_APP_PRIVATE_KEY` | Backend | GitHub App RSA Private Key |
| `GITHUB_CLIENT_ID` | Backend | GitHub OAuth Client ID |
| `GITHUB_CLIENT_SECRET` | Backend | GitHub OAuth Client Secret |
| `JWT_SECRET_KEY` | Backend | Secret key for JWT session tokens |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend | Backend API endpoint URL (`http://127.0.0.1:8000`) |

---

## Automated Test Verification

### Backend Test Suite (142 Tests)

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m compileall app
```

### Frontend Quality & Production Build

```bash
cd frontend
npm run lint
npm run build
```

---

## Deployment & Production

Deploy CodeSage AI using Docker Compose or Kubernetes:

```bash
# Production Docker Compose Stack
docker compose -f docker-compose.prod.yml up -d --build

# Kubernetes Deployments
kubectl apply -f k8s/
```

Refer to [`docs/DEPLOYMENT_GUIDE.md`](file:///c:/Users/tejas/codesage-ai/docs/DEPLOYMENT_GUIDE.md) for detailed environment configuration, TLS setup, and database migration steps.

---

## Current Status

**v1.0 — Feature Complete & Verified Green**.

All 142 backend tests and 15 frontend App Router routes are fully tested, integrated, and ready for production deployment.

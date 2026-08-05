# CodeSage AI — REST API Reference Manual

This document details the REST API endpoints provided by the **CodeSage AI** FastAPI backend.

Interactive OpenAPI documentation is generated dynamically at runtime:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## Endpoint Summary Matrix

| Group | Method | Path | Description |
| :--- | :--- | :--- | :--- |
| **Health** | `GET` | `/health` | Primary health check probe |
| **Health** | `GET` | `/liveness` | Kubernetes liveness probe |
| **Health** | `GET` | `/readiness` | Kubernetes readiness probe (checks DB & Redis connections) |
| **Health** | `GET` | `/metrics` | Prometheus metrics scrape endpoint |
| **Webhooks** | `POST` | `/webhook` | GitHub App HMAC signed webhook receiver |
| **Dashboard**| `GET` | `/api/dashboard` | Top-level summary metrics across repos, PRs, & reviews |
| **Repos** | `GET` | `/api/repositories` | List monitored repositories |
| **Repos** | `GET` | `/api/repositories/{owner}/{repo}` | Detailed repository summary and active PRs |
| **Repos** | `GET` | `/api/repositories/{owner}/{repo}/pulls/{number}` | Pull request details and AI review findings |
| **Jobs** | `GET` | `/api/jobs` | Query background review jobs |
| **Jobs** | `GET` | `/api/jobs/{job_id}` | Fetch status for specific review job |
| **Jobs** | `POST` | `/api/jobs/{job_id}/cancel` | Cancel queued or running review job |
| **Auth** | `GET` | `/api/auth/github/login` | Returns GitHub OAuth authorization URL |
| **Auth** | `GET` | `/api/auth/github/callback` | OAuth callback endpoint; sets session cookie |
| **Auth** | `GET` | `/api/auth/me` | Returns current user profile and assigned role |
| **Auth** | `POST` | `/api/auth/logout` | Clears session cookie and logs user out |
| **Installations** | `GET` | `/api/installations` | List GitHub App installations |
| **AI Platform** | `GET` | `/api/ai/providers` | Query active LLM providers and models |
| **AI Platform** | `GET` | `/api/ai/prompts` | List active prompt templates |
| **Search** | `POST` | `/api/repository-intelligence/index` | Trigger repository codebase indexing |
| **Search** | `GET` | `/api/repository-intelligence/search` | Execute hybrid RRF code search |
| **Policies** | `GET` | `/api/policies` | List active review policies |
| **Policies** | `GET` | `/api/policies/effective/{owner}/{repo}` | Resolves effective policy for a repository |
| **Analytics** | `GET` | `/api/analytics/overview` | Engineering overview metrics |
| **Analytics** | `GET` | `/api/analytics/reviews` | Review turnaround and approval rates |
| **Analytics** | `GET` | `/api/analytics/findings` | Finding breakdown by severity level and category |
| **Analytics** | `GET` | `/api/analytics/ai-usage` | Token consumption, USD costs, and provider usage |
| **Analytics** | `GET` | `/api/analytics/jobs` | Job queue status breakdown and success rate |
| **Audit Log** | `GET` | `/api/audit-events` | Paginated immutable audit trail with filters |

---

## Key API Models & Payloads

### GET /api/analytics/overview
```json
{
  "total_repositories": 12,
  "total_pull_requests": 48,
  "total_reviews": 45,
  "total_findings": 18
}
```

### GET /api/audit-events
```json
{
  "total": 120,
  "limit": 50,
  "offset": 0,
  "events": [
    {
      "id": 1,
      "event_type": "user.login",
      "actor": "Tejas190605",
      "description": "User logged in via GitHub OAuth.",
      "metadata": { "ip": "127.0.0.1" },
      "created_at": "2026-08-05T09:15:00Z"
    }
  ]
}
```

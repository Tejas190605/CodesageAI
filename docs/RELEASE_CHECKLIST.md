# CodeSage AI v1.0 Release Checklist

This document separates **Local Portfolio Development Ready** verification from **Real Production Infrastructure Deployment** pre-flight steps.

---

## Part 1: Local Portfolio Development Verification

- [x] **Backend Pytest Suite**: 142/142 tests passing (`python -m pytest -q`).
- [x] **Backend App Compilation**: Zero syntax errors (`python -m compileall app`).
- [x] **Frontend ESLint Audit**: 0 errors, 0 warnings (`npm run lint`).
- [x] **Frontend Production Build**: 15 App Router static routes compiled successfully (`npm run build`).
- [x] **Alembic Migration Chain**: Linear chain `001` through `007` validated on clean schema head (`alembic upgrade head`).
- [x] **End-to-End Subsystem Connectivity**: Webhook $\rightarrow$ Queue $\rightarrow$ Worker $\rightarrow$ RAG $\rightarrow$ Policy $\rightarrow$ LLM $\rightarrow$ Publisher $\rightarrow$ DB $\rightarrow$ Analytics $\rightarrow$ Audit $\rightarrow$ Dashboard verified green.
- [x] **Security & Secret Scrubbing**: Zero tracked secrets (`.env`, private keys, JWT secrets, tokens) in Git index.
- [x] **Documentation Complete**: `README.md`, `ARCHITECTURE.md`, `LOCAL_DEVELOPMENT.md`, `DEPLOYMENT_GUIDE.md`, `API.md`, `SECURITY.md`, and `RELEASE_NOTES_v1.0.md` created and updated.

**LOCAL PORTFOLIO STATUS**: **READY FOR RELEASE (PASS)**.

---

## Part 2: Real Production Infrastructure Deployment Pre-Flight Checklist

*The following steps require external cloud credentials, domain DNS, TLS certificates, and a live GitHub App configuration.*

- [ ] **Infrastructure Provisioning**:
  - [ ] PostgreSQL 15+ instance running with `pgvector` extension enabled.
  - [ ] Redis 6.0+ instance accessible by worker processes.
- [ ] **GitHub App Configuration**:
  - [ ] Registered GitHub App with `Pull Requests (Read & Write)` and `Contents (Read)` permissions.
  - [ ] Webhook URL pointed to `https://<api-domain>/webhook` with `GITHUB_WEBHOOK_SECRET` set.
  - [ ] OAuth Callback URL set to `https://<app-domain>/api/auth/github/callback`.
- [ ] **Environment Secrets Injection**:
  - [ ] `DATABASE_URL` configured with production database credentials.
  - [ ] `REDIS_URL` configured.
  - [ ] `GEMINI_API_KEY` or LLM credentials injected securely.
  - [ ] `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_CLIENT_ID`, and `GITHUB_CLIENT_SECRET` injected.
  - [ ] `JWT_SECRET_KEY` set to strong random string.
- [ ] **Networking & TLS**:
  - [ ] Domain DNS configured (`A` / `CNAME` records pointing to Ingress / Load Balancer).
  - [ ] TLS certificate issued via Let's Encrypt / Cert-Manager / AWS ACM.
- [ ] **Production Deployment Execution**:
  - [ ] Execute `alembic upgrade head` on production PostgreSQL database.
  - [ ] Apply Kubernetes manifests (`kubectl apply -f k8s/`) or start Docker Compose (`docker compose -f docker-compose.prod.yml up -d`).
  - [ ] Verify health endpoints (`/health`, `/liveness`, `/readiness`).

**REAL PRODUCTION STATUS**: **REQUIRES EXTERNAL INFRASTRUCTURE SETUP**.

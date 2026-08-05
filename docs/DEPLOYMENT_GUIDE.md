# CodeSage AI — Production Deployment Guide

This guide covers production deployment for **CodeSage AI** using **Docker Compose** and **Kubernetes**.

---

## 1. Pre-Deployment Infrastructure Prerequisites

Before deploying CodeSage AI to production, ensure the following infrastructure resources are provisioned:
1. **PostgreSQL Database**: PostgreSQL 15+ instance with the `pgvector` extension enabled (`CREATE EXTENSION IF NOT EXISTS vector;`).
2. **Redis Cache / Broker**: Redis 6.0+ instance for background job queuing.
3. **GitHub App**: Registered GitHub App with `Pull Requests (Read & Write)` and `Contents (Read)` permissions.
4. **Domain & TLS Certificate**: Valid FQDN (e.g. `codesage.example.com`) with TLS termination via Ingress or Reverse Proxy.

---

## 2. Environment Secrets Setup

Create production secrets securely in your orchestrator or secret manager. Never store real secrets in Git repositories.

### Required Secrets Checklist

```env
DATABASE_URL=postgresql://codesage_user:<SECURE_PASSWORD>@postgres.prod.internal:5432/codesage_prod
REDIS_URL=redis://redis.prod.internal:6379/0

GEMINI_API_KEY=<PRODUCTION_GEMINI_API_KEY>
GITHUB_WEBHOOK_SECRET=<PRODUCTION_HMAC_SECRET>

GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="<PRODUCTION_GITHUB_APP_RSA_PRIVATE_KEY_PEM>"

GITHUB_CLIENT_ID=<PRODUCTION_OAUTH_CLIENT_ID>
GITHUB_CLIENT_SECRET=<PRODUCTION_OAUTH_CLIENT_SECRET>

JWT_SECRET_KEY=<SECURE_RANDOM_256BIT_KEY>
NEXT_PUBLIC_API_BASE_URL=https://api.codesage.example.com
```

---

## 3. Database Migration Deployment

Before routing production traffic to backend containers, execute database migrations:

```bash
docker run --rm \
  --env-file .env.production \
  codesage-backend:v1.0.0 \
  python -m alembic upgrade head
```

Verify migration status:

```bash
docker run --rm \
  --env-file .env.production \
  codesage-backend:v1.0.0 \
  python -m alembic current
```

---

## 4. Docker Compose Production Deployment

Deploy using the production Compose stack definition:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Health Verification

```bash
curl -f https://api.codesage.example.com/health
curl -f https://api.codesage.example.com/liveness
curl -f https://api.codesage.example.com/readiness
```

---

## 5. Kubernetes Production Deployment

Apply Kubernetes manifests located in `k8s/`:

```bash
# 1. Apply Namespace, ConfigMap, and Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 2. Deploy Services & Applications
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### Check Pod Status & Scaling

```bash
kubectl get pods -n codesage-ai
kubectl get hpa -n codesage-ai
```

---

## 6. GitHub App & Webhook Configuration

1. In GitHub App Settings $\rightarrow$ **Webhook**:
   - **Webhook URL**: `https://api.codesage.example.com/webhook`
   - **Secret**: Enter the exact value configured in `GITHUB_WEBHOOK_SECRET`.
2. In GitHub App Settings $\rightarrow$ **User Authorization Callback URL**:
   - **Callback URL**: `https://app.codesage.example.com/api/auth/github/callback`

---

## 7. Rollback & Emergency Procedures

If a deployment fails:
1. **Revert Kubernetes Deployment**: `kubectl rollout undo deployment/codesage-backend -n codesage-ai`
2. **Database Rollback**: Execute targeted Alembic downgrade commands using test migration backups.
3. **Queue Drain**: Flush non-critical queued jobs using `redis-cli -u $REDIS_URL FLUSHDB`.

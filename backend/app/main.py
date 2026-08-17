import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.config import settings
from app.database import init_db
from app.routes.github_webhooks import router as github_router
from app.routes.api import router as api_router
from app.routes.jobs import router as jobs_router
from app.routes.auth import router as auth_router
from app.routes.installations import router as installations_router
from app.routes.health import router as health_router
from app.routes.ai_platform import router as ai_platform_router
from app.routes.repository_intelligence import router as repo_intelligence_router
from app.routes.policies import router as policies_router
from app.routes.analytics import router as analytics_router
from app.routes.audit import router as audit_router
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.security import ProductionSecurityMiddleware
from app.worker import run_worker_loop

# Configure standard Python logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("codesage.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager initializing database schema, syncing installations & launching worker loop."""
    init_db()
    try:
        from app.database import SessionLocal
        from app.services.github_app_service import sync_installations_and_repositories
        with SessionLocal() as db:
            sync_installations_and_repositories(db)
    except Exception as e:
        logger.warning(f"Initial installation sync skipped: {e}")

    worker_task = asyncio.create_task(run_worker_loop())
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="CodeSage AI",
    description="AI-powered GitHub Pull Request code review assistant and developer dashboard API",
    version="1.4.0",
    lifespan=lifespan
)

# 1. Security Hardening & Rate Limiting Middleware
app.add_middleware(ProductionSecurityMiddleware)

# 2. Correlation ID Distributed Tracing Middleware
app.add_middleware(CorrelationIdMiddleware)

# 3. GZip Response Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. CORS Middleware for Frontend Next.js / Vite web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home() -> Dict[str, str]:
    """Root status endpoint."""
    return {"message": "CodeSage AI is running 🚀"}


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint for status monitoring and orchestrator probes."""
    return {
        "status": "ok",
        "service": "codesage-ai"
    }


# Include Routers
app.include_router(health_router)
app.include_router(github_router)
app.include_router(api_router)
app.include_router(jobs_router)
app.include_router(auth_router)
app.include_router(installations_router)
app.include_router(ai_platform_router)
app.include_router(repo_intelligence_router)
app.include_router(policies_router)
app.include_router(analytics_router)
app.include_router(audit_router)

logger.info(f"CodeSage AI FastAPI application initialized (CORS origins: {settings.cors_origins_list}).")
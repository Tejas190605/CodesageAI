import logging
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.github_webhooks import router as github_router
from app.routes.api import router as api_router

# Configure standard Python logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("codesage.main")

app = FastAPI(
    title="CodeSage AI",
    description="AI-powered GitHub Pull Request code review assistant and developer dashboard API",
    version="0.3.0"
)

# Configure CORS Middleware for Frontend Next.js / Vite web apps
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
app.include_router(github_router)
app.include_router(api_router)

logger.info(f"CodeSage AI FastAPI application initialized (CORS origins: {settings.cors_origins_list}).")
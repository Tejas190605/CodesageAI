import logging
from typing import Dict
from fastapi import FastAPI
from app.routes.github_webhooks import router as github_router

# Configure standard Python logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("codesage.main")

app = FastAPI(
    title="CodeSage AI",
    description="AI-powered GitHub Pull Request code review assistant",
    version="0.2.0"
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


app.include_router(github_router)

logger.info("CodeSage AI FastAPI application initialized.")
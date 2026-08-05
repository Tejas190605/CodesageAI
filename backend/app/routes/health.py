import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge
from app.database import get_db
from app.services.redis_manager import get_redis_client

logger = logging.getLogger("codesage.routes.health")

router = APIRouter(tags=["Health & Observability"])

# Prometheus Metrics Definitions
HTTP_REQUEST_COUNTER = Counter(
    "codesage_http_requests_total",
    "Total HTTP requests processed",
    ["method", "endpoint", "status_code"]
)
REVIEW_JOBS_COUNTER = Counter(
    "codesage_review_jobs_total",
    "Total background review jobs processed",
    ["status"]
)
QUEUE_DEPTH_GAUGE = Gauge(
    "codesage_queue_depth",
    "Current background review job queue depth"
)


@router.get("/liveness")
def liveness_probe() -> Dict[str, str]:
    """Liveness probe checking basic process heartbeat."""
    return {"status": "alive", "service": "codesage-backend"}


@router.get("/readiness")
def readiness_probe(db: Session = Depends(get_db), response: Response = None) -> Dict[str, Any]:
    """
    Readiness probe validating database and Redis connectivity before routing traffic.
    Returns 200 OK when dependencies are healthy, 503 Service Unavailable when degraded.
    """
    health_details = {
        "status": "ready",
        "database": "unhealthy",
        "redis": "unhealthy"
    }

    # 1. Probe Database Connection
    try:
        db.execute(text("SELECT 1"))
        health_details["database"] = "healthy"
    except Exception as e:
        logger.error(f"Readiness probe database check failed: {e}")
        health_details["status"] = "unhealthy"

    # 2. Probe Redis Connection
    try:
        redis_client = get_redis_client()
        if redis_client and redis_client.ping():
            health_details["redis"] = "healthy"
        else:
            health_details["redis"] = "fallback_memory"
    except Exception as e:
        logger.warning(f"Readiness probe Redis check warning: {e}")
        health_details["redis"] = "fallback_memory"

    if health_details["status"] == "unhealthy" and response:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_details


@router.get("/metrics")
def prometheus_metrics():
    """Returns Prometheus formatted operational metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

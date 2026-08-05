import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("codesage.middleware.correlation")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware ensuring every HTTP request has a unique X-Correlation-ID header
    for distributed tracing and structured log aggregation across services.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or f"corr-{uuid.uuid4().hex[:12]}"
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

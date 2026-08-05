import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, List
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("codesage.middleware.security")

# Rate Limiter Configuration: 100 requests per 60 seconds per IP
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60

_IP_REQUEST_HISTORY: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    """Sliding window rate limit check per client IP."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    # Clean old entries
    timestamps = [ts for ts in _IP_REQUEST_HISTORY[client_ip] if ts > cutoff]
    _IP_REQUEST_HISTORY[client_ip] = timestamps

    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        return False

    _IP_REQUEST_HISTORY[client_ip].append(now)
    return True


class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    """
    Production security hardening middleware:
    - Enforces Security Headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
    - IP Rate Limiting for DDoS protection
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Apply Rate Limiting (exempt /health, /metrics, /readiness, /liveness)
        if request.url.path not in ["/health", "/metrics", "/readiness", "/liveness"]:
            if not check_rate_limit(client_ip):
                logger.warning(f"Rate limit exceeded for IP: {client_ip} on path {request.url.path}")
                return Response(
                    content='{"detail": "Rate limit exceeded. Please try again later."}',
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                    headers={"Retry-After": "60"}
                )

        response = await call_next(request)

        # Inject Security Hardening Response Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none';"

        return response

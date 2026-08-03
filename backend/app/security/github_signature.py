import hmac
import hashlib
import logging
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger("codesage.security")


def verify_github_signature(signature_header: str | None, body: bytes) -> None:
    """
    Verifies that an incoming GitHub webhook request was signed with the configured secret.
    Uses HMAC-SHA256 and constant-time digest comparison to prevent timing attacks.

    Raises:
        HTTPException(500): If the webhook secret is not configured in settings.
        HTTPException(401): If signature header is missing or signature is invalid.
    """
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        logger.error("GITHUB_WEBHOOK_SECRET is missing from server configuration.")
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured on server."
        )

    if not signature_header:
        logger.warning("Rejecting webhook request: Missing X-Hub-Signature-256 header.")
        raise HTTPException(
            status_code=401,
            detail="Missing GitHub signature."
        )

    expected_signature = (
        "sha256="
        + hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(expected_signature, signature_header):
        logger.warning("Rejecting webhook request: Signature mismatch.")
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub signature."
        )

    logger.debug("GitHub webhook signature successfully verified.")
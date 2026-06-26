import os
import hmac
import hashlib

from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")


def verify_github_signature(signature_header: str, body: bytes):

    if not WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Webhook secret not configured."
        )

    if not signature_header:
        raise HTTPException(
            status_code=401,
            detail="Missing GitHub signature."
        )

    expected_signature = (
        "sha256="
        + hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(
        expected_signature,
        signature_header
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub signature."
        )
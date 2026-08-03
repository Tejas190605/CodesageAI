import hmac
import hashlib
import pytest
from fastapi import HTTPException
from app.security.github_signature import verify_github_signature


def _generate_signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_valid_signature(dummy_secret):
    """Tests that a valid HMAC SHA-256 signature passes verification."""
    body = b'{"action": "opened", "number": 1}'
    valid_sig = _generate_signature(dummy_secret, body)

    # Should complete without raising any exception
    verify_github_signature(valid_sig, body)


def test_invalid_signature_rejected(dummy_secret):
    """Tests that an incorrect signature raises HTTP 401."""
    body = b'{"action": "opened"}'
    invalid_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    with pytest.raises(HTTPException) as exc_info:
        verify_github_signature(invalid_sig, body)

    assert exc_info.value.status_code == 401
    assert "Invalid GitHub signature" in exc_info.value.detail


def test_missing_signature_rejected():
    """Tests that a missing signature header raises HTTP 401."""
    body = b'{"action": "opened"}'

    with pytest.raises(HTTPException) as exc_info:
        verify_github_signature(None, body)

    assert exc_info.value.status_code == 401
    assert "Missing GitHub signature" in exc_info.value.detail


def test_tampered_payload_rejected(dummy_secret):
    """Tests that a modified payload with the original signature fails verification."""
    original_body = b'{"action": "opened", "number": 1}'
    sig = _generate_signature(dummy_secret, original_body)

    tampered_body = b'{"action": "opened", "number": 2}'

    with pytest.raises(HTTPException) as exc_info:
        verify_github_signature(sig, tampered_body)

    assert exc_info.value.status_code == 401


def test_signature_missing_prefix_rejected(dummy_secret):
    """Tests that a signature missing the 'sha256=' prefix is rejected."""
    body = b'{"action": "opened"}'
    raw_hash = hmac.new(dummy_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

    with pytest.raises(HTTPException) as exc_info:
        verify_github_signature(raw_hash, body)

    assert exc_info.value.status_code == 401

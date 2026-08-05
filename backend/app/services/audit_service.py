import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.db import AuditEvent

logger = logging.getLogger("codesage.audit_service")

SENSITIVE_KEYS = {
    "token", "secret", "password", "authorization", "cookie",
    "api_key", "private_key", "access_token", "github_token",
    "credentials", "key", "auth", "jwt"
}


def sanitize_metadata(data: Any) -> Any:
    """
    Recursively scrubs sensitive keys (tokens, secrets, credentials, API keys)
    from audit event metadata JSON payloads.
    """
    if isinstance(data, dict):
        clean_dict = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in SENSITIVE_KEYS):
                clean_dict[k] = "[REDACTED_SENSITIVE_DATA]"
            else:
                clean_dict[k] = sanitize_metadata(v)
        return clean_dict
    elif isinstance(data, list):
        return [sanitize_metadata(item) for item in data]
    return data


def record_event(
    db: Session,
    event_type: str,
    actor: str = "system",
    organization_id: Optional[int] = None,
    repository_id: Optional[int] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[AuditEvent]:
    """
    Records an application audit event safely in the database.
    Catches exceptions gracefully to prevent audit logging failures from breaking main app flows.
    """
    try:
        clean_meta = sanitize_metadata(metadata) if metadata else None
        event_rec = AuditEvent(
            event_type=event_type,
            actor=actor,
            organization_id=organization_id,
            repository_id=repository_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            metadata_json=clean_meta
        )
        db.add(event_rec)
        db.commit()
        db.refresh(event_rec)
        logger.info(f"Recorded audit event '{event_type}' (actor={actor}, resource={resource_type}:{resource_id}).")
        return event_rec
    except Exception as e:
        logger.error(f"Failed to record audit event '{event_type}': {e}", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
        return None

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.db import AuditEvent

logger = logging.getLogger("codesage.routes.audit")

router = APIRouter(prefix="/api/audit-events", tags=["Audit Log"])


@router.get("")
def read_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event_type"),
    repository_id: Optional[int] = Query(None, description="Filter by repository_id"),
    organization_id: Optional[int] = Query(None, description="Filter by organization_id"),
    user_id: Optional[int] = Query(None, description="Filter by user_id"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieves paginated audit events ordered by created_at DESC."""
    query_stmt = db.query(AuditEvent)

    if event_type:
        query_stmt = query_stmt.filter(AuditEvent.event_type == event_type)
    if repository_id:
        query_stmt = query_stmt.filter(AuditEvent.repository_id == repository_id)
    if organization_id:
        query_stmt = query_stmt.filter(AuditEvent.organization_id == organization_id)
    if user_id:
        query_stmt = query_stmt.filter(AuditEvent.user_id == user_id)

    total_count = query_stmt.count()
    events = query_stmt.order_by(AuditEvent.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "events": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "actor": ev.actor,
                "organization_id": ev.organization_id,
                "repository_id": ev.repository_id,
                "user_id": ev.user_id,
                "resource_type": ev.resource_type,
                "resource_id": ev.resource_id,
                "description": ev.description,
                "metadata": ev.metadata_json,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in events
        ]
    }

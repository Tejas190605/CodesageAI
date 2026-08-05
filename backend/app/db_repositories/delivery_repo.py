from typing import Optional
from sqlalchemy.orm import Session
from app.models.db import WebhookDelivery


def is_delivery_processed(db: Session, delivery_id: str) -> bool:
    """Checks whether a GitHub delivery ID has already been recorded in database."""
    if not delivery_id:
        return False
    delivery = db.query(WebhookDelivery).filter(
        WebhookDelivery.delivery_id == delivery_id.strip()
    ).first()
    return delivery is not None and delivery.processed


def record_delivery_in_db(
    db: Session,
    delivery_id: str,
    status: str = "received",
    processed: bool = True
) -> Optional[WebhookDelivery]:
    """Records a new GitHub Webhook Delivery ID to ensure database idempotency."""
    if not delivery_id:
        return None
    d_clean = delivery_id.strip()
    delivery = db.query(WebhookDelivery).filter(
        WebhookDelivery.delivery_id == d_clean
    ).first()

    if not delivery:
        delivery = WebhookDelivery(
            delivery_id=d_clean,
            processed=processed,
            status=status
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
    return delivery

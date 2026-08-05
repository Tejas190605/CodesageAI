import logging
import threading
from collections import OrderedDict
from typing import Optional
from app.database import SessionLocal
from app.db_repositories.delivery_repo import is_delivery_processed, record_delivery_in_db

logger = logging.getLogger("codesage.delivery_tracker")

DEFAULT_CAPACITY = 1000


class DeliveryTracker:
    """
    Thread-safe delivery tracker for webhook idempotency.
    Combines an in-memory LRU cache with database persistence (`WebhookDelivery`).
    Prevents duplicate background processing when GitHub redelivers webhooks.
    """

    def __init__(self, capacity: int = DEFAULT_CAPACITY, persist_to_db: bool = True):
        self.capacity = max(1, capacity)
        self.persist_to_db = persist_to_db
        self._deliveries: OrderedDict[str, bool] = OrderedDict()
        self._lock = threading.Lock()

    def is_duplicate(self, delivery_id: str) -> bool:
        """Checks if a delivery ID has already been recorded in memory or database."""
        if not delivery_id:
            return False
        with self._lock:
            if delivery_id in self._deliveries:
                return True

        if not self.persist_to_db:
            return False

        # Check DB fallback if missing from LRU memory cache
        try:
            with SessionLocal() as db:
                if is_delivery_processed(db, delivery_id):
                    with self._lock:
                        self._deliveries[delivery_id] = True
                    return True
        except Exception as e:
            logger.warning(f"Error checking DB for delivery_id '{delivery_id}': {e}")

        return False

    def record_delivery(self, delivery_id: str) -> bool:
        """
        Records a new delivery ID in memory and database if not already present.
        Returns True if newly recorded, False if already present (duplicate).
        """
        if not delivery_id:
            return False

        if self.is_duplicate(delivery_id):
            return False

        with self._lock:
            self._deliveries[delivery_id] = True
            self._deliveries.move_to_end(delivery_id)
            if len(self._deliveries) > self.capacity:
                self._deliveries.popitem(last=False)

        if self.persist_to_db:
            try:
                with SessionLocal() as db:
                    record_delivery_in_db(db, delivery_id, status="received", processed=True)
            except Exception as e:
                logger.warning(f"Error persisting delivery_id '{delivery_id}' to DB: {e}")

        return True

    def clear(self) -> None:
        """Resets tracked memory delivery IDs (used for test isolation)."""
        with self._lock:
            self._deliveries.clear()


# Global singleton instance
_tracker_instance = DeliveryTracker()


def is_duplicate_delivery(delivery_id: Optional[str]) -> bool:
    """Returns True if delivery_id has already been processed."""
    if not delivery_id:
        return False
    return _tracker_instance.is_duplicate(delivery_id)


def record_delivery(delivery_id: Optional[str]) -> bool:
    """Records delivery_id into global tracker. Returns True if new, False if duplicate."""
    if not delivery_id:
        return False
    return _tracker_instance.record_delivery(delivery_id)


def reset_delivery_tracker() -> None:
    """Resets global delivery tracker (test helper)."""
    _tracker_instance.clear()

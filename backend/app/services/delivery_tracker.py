import logging
import threading
from collections import OrderedDict
from typing import Optional

logger = logging.getLogger("codesage.delivery_tracker")

# Default bounded capacity for recent webhook delivery IDs
DEFAULT_CAPACITY = 1000


class DeliveryTracker:
    """
    Thread-safe, in-memory LRU delivery tracker for webhook idempotency.
    Prevents duplicate background processing when GitHub redelivers webhooks.
    """

    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self.capacity = max(1, capacity)
        self._deliveries: OrderedDict[str, bool] = OrderedDict()
        self._lock = threading.Lock()

    def is_duplicate(self, delivery_id: str) -> bool:
        """Checks if a delivery ID has already been recorded without modifying state."""
        if not delivery_id:
            return False
        with self._lock:
            return delivery_id in self._deliveries

    def record_delivery(self, delivery_id: str) -> bool:
        """
        Records a new delivery ID if not already present.
        Evicts the oldest delivery ID when capacity is exceeded.

        Returns:
            True if the delivery ID was newly recorded.
            False if it was already present (duplicate).
        """
        if not delivery_id:
            return False

        with self._lock:
            if delivery_id in self._deliveries:
                return False

            self._deliveries[delivery_id] = True
            # Move to end to maintain LRU order
            self._deliveries.move_to_end(delivery_id)

            # Evict oldest entry if capacity exceeded
            if len(self._deliveries) > self.capacity:
                self._deliveries.popitem(last=False)

            return True

    def clear(self) -> None:
        """Resets tracked delivery IDs (used for test isolation)."""
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

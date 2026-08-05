import time
import logging
from typing import Callable, Any, TypeVar, Optional

logger = logging.getLogger("codesage.circuit_breaker")

T = TypeVar("T")


class CircuitBreakerOpenException(Exception):
    """Raised when an external API call is blocked because the Circuit Breaker is OPEN."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation for external service integration resiliency
    (GitHub API, Gemini LLM API).
    States:
    - CLOSED: Normal operation. All calls pass through.
    - OPEN: Service failing. Calls fail fast without calling remote service.
    - HALF_OPEN: Recovery testing. Single probe call allowed to check recovery.
    """
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_state_change = time.time()

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes the wrapped function through the circuit breaker state machine."""
        now = time.time()

        if self.state == "OPEN":
            if now - self.last_state_change > self.recovery_timeout_seconds:
                logger.info(f"CircuitBreaker [{self.name}] transitioning OPEN -> HALF_OPEN (probing recovery).")
                self.state = "HALF_OPEN"
                self.last_state_change = now
            else:
                raise CircuitBreakerOpenException(
                    f"CircuitBreaker [{self.name}] is OPEN. Call blocked to prevent cascading failures."
                )

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                logger.info(f"CircuitBreaker [{self.name}] probe succeeded. Transitioning HALF_OPEN -> CLOSED.")
                self.state = "CLOSED"
                self.failure_count = 0
                self.last_state_change = now
            elif self.state == "CLOSED":
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            logger.warning(f"CircuitBreaker [{self.name}] failure recorded ({self.failure_count}/{self.failure_threshold}): {e}")
            if self.failure_count >= self.failure_threshold:
                logger.error(f"CircuitBreaker [{self.name}] failure threshold reached. Transitioning -> OPEN.")
                self.state = "OPEN"
                self.last_state_change = now
            raise e


# Shared Singleton Circuit Breakers
github_api_circuit_breaker = CircuitBreaker("GitHub_API", failure_threshold=5, recovery_timeout_seconds=30.0)
gemini_ai_circuit_breaker = CircuitBreaker("Gemini_AI", failure_threshold=3, recovery_timeout_seconds=60.0)

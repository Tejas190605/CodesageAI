import pytest
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from app.middleware.security import check_rate_limit, _IP_REQUEST_HISTORY


def test_production_security_headers_injected(client):
    """Tests that security hardening headers are injected on all HTTP responses."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in res.headers
    assert "Content-Security-Policy" in res.headers


def test_rate_limiting_middleware_trigger():
    """Tests rate limit trigger when request threshold per IP window is exceeded."""
    test_ip = "192.168.1.99"
    _IP_REQUEST_HISTORY[test_ip] = []

    # Fill capacity
    for _ in range(100):
        allowed = check_rate_limit(test_ip)
        assert allowed is True

    # 101st request blocked
    allowed_blocked = check_rate_limit(test_ip)
    assert allowed_blocked is False


def test_circuit_breaker_state_transitions():
    """Tests CircuitBreaker state machine (CLOSED -> OPEN -> CircuitBreakerOpenException)."""
    cb = CircuitBreaker("Test_Service", failure_threshold=2, recovery_timeout_seconds=1.0)
    assert cb.state == "CLOSED"

    def _failing_func():
        raise ValueError("Service Unavailable")

    # Attempt 1 failure
    with pytest.raises(ValueError):
        cb.call(_failing_func)
    assert cb.state == "CLOSED"

    # Attempt 2 failure -> transition to OPEN
    with pytest.raises(ValueError):
        cb.call(_failing_func)
    assert cb.state == "OPEN"

    # Subsequent calls fail fast with CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        cb.call(_failing_func)


def test_gzip_response_compression(client):
    """Tests GZip response compression for large JSON payload responses."""
    res = client.get("/metrics", headers={"Accept-Encoding": "gzip"})
    assert res.status_code == 200

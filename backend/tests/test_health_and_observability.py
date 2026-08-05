import pytest


def test_liveness_probe_endpoint(client):
    """Tests the /liveness process heartbeat endpoint."""
    res = client.get("/liveness")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"
    assert res.json()["service"] == "codesage-backend"


def test_readiness_probe_endpoint(client):
    """Tests the /readiness database & Redis dependency probe."""
    res = client.get("/readiness")
    assert res.status_code == 200
    json_resp = res.json()
    assert json_resp["status"] == "ready"
    assert json_resp["database"] == "healthy"


def test_prometheus_metrics_endpoint(client):
    """Tests the /metrics Prometheus metric exporter endpoint."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "codesage_http_requests_total" in res.text or "python_gc_objects_collected_total" in res.text


def test_correlation_id_middleware(client):
    """Tests that X-Correlation-ID header is generated and injected on all responses."""
    res = client.get("/")
    assert res.status_code == 200
    assert "X-Correlation-ID" in res.headers
    assert res.headers["X-Correlation-ID"].startswith("corr-")

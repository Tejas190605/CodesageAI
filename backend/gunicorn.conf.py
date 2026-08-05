import os

# Production Gunicorn server configuration for FastAPI
bind = os.environ.get("BIND", "0.0.0.0:8000")
workers = int(os.environ.get("WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout & Shutdown Tuning
timeout = int(os.environ.get("TIMEOUT", "300"))
graceful_timeout = int(os.environ.get("GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("KEEPALIVE", "5"))

# Logging Config
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

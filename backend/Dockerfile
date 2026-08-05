# Multi-Stage Production Dockerfile for CodeSage AI FastAPI Backend

# Stage 1: Build Dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Stage 2: Runtime Container
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/codesage/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Run container as non-root user for security hardening
RUN useradd -m -u 10001 codesage && \
    chown -R codesage:codesage /app

USER codesage

COPY --chown=codesage:codesage --from=builder /root/.local /home/codesage/.local
COPY --chown=codesage:codesage . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/readiness || exit 1

CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]

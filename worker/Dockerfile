# Production Dockerfile for CodeSage AI Background Worker

FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/codesage/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 10001 codesage && \
    chown -R codesage:codesage /app

USER codesage

COPY --chown=codesage:codesage --from=builder /root/.local /home/codesage/.local
COPY --chown=codesage:codesage backend/ .

CMD ["python", "-m", "app.worker"]

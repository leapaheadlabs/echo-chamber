# ── ECHO CHAMBER — Cortex + Commander ─────────────────────────────────────
# Multi-stage build: builder (compile deps) → runtime (lean)

FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.0
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock* ./

# Install all deps (virtualenv=False for container)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main || \
    poetry install --no-interaction --no-ansi

# ── Runtime ───────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r echo && useradd -r -g echo -d /app echo

WORKDIR /app

# Copy installed packages from builder (read+execute, no write)
COPY --from=builder --chmod=755 /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder --chmod=755 /usr/local/bin /usr/local/bin

# Copy application code (read+execute, no write — runtime is immutable)
COPY --chown=echo:echo --chmod=555 src/ ./src/

USER echo

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "echo_chamber.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]

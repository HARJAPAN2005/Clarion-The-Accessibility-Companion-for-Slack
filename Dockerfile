# syntax=docker/dockerfile:1
# =============================================================================
# Clarion — Multi-stage Dockerfile
# =============================================================================
# Build:  docker build -t clarion:latest .
# Run:    docker run --rm --env-file .env clarion:latest
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Build dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files needed for dependency resolution first (better cache).
COPY requirements.txt pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — Runtime image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN addgroup --system clarion \
    && adduser --system --ingroup clarion --no-create-home clarion

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=clarion:clarion . .

# Runtime user
USER clarion

# Health check — verify the process is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import app" || exit 1

# Default command: Socket Mode
CMD ["python", "app.py"]

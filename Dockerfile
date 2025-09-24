# Multi-stage production Dockerfile for CMP Financial AI Platform
# Optimized for security, performance, and minimal image size

# Build stage - Python dependencies and ML models
FROM python:3.13-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage - Minimal runtime environment
FROM python:3.13-slim as production

# Set labels for container metadata
LABEL maintainer="CMP Team" \
      description="CMP Financial AI Platform - Production" \
      version="${VERSION:-latest}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    ENV=production \
    WORKERS=4 \
    PORT=8000

# Install only runtime system dependencies + Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r cmp && useradd -r -g cmp -u 1001 cmp

# Create application directory and set ownership
WORKDIR /app
RUN chown -R cmp:cmp /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=cmp:cmp . .

# Create required directories with proper permissions
RUN mkdir -p logs local_storage/bank_statements local_storage/invoices local_storage/ml_models && \
    chown -R cmp:cmp logs local_storage

# Switch to non-root user
USER cmp

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Expose application port
EXPOSE $PORT

# Production startup command with Gunicorn
CMD ["sh", "-c", "gunicorn cmp.main:app -w ${WORKERS} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT} --access-logfile - --error-logfile - --log-level info"]
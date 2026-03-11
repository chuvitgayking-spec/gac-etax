# ============================================================================
# E-Tax Invoice System Dockerfile
# Production-ready with multi-stage build
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: Builder
# ----------------------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /build

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ----------------------------------------------------------------------------
# Stage 2: Production
# ----------------------------------------------------------------------------
FROM python:3.11-slim

# Labels
LABEL maintainer="GAC Thailand"
LABEL description="E-Tax Invoice System"

# Security: Run as non-root user
RUN groupadd -r etax && useradd -r -g etax etax

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/etax/.local

# Copy application
COPY --chown=etax:etax . .

# Create directories
RUN mkdir -p /data /logs /secure/keys && \
    chown -R etax:etax /app /data /logs

# Set environment
ENV PATH=/home/etax/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run as non-root
USER etax

# Entrypoint
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

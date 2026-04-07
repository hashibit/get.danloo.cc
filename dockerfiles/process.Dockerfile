# ==========================================
# Multi-stage build for Process service
# ==========================================

# ==========================================
# Stage 1: Build dependencies and install packages
# ==========================================
FROM python:3.11-slim as builder

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml uv.lock* ./

# Copy source code
COPY common/ ./common/
COPY process/ ./process/

# Install dependencies and create a virtual environment
RUN uv sync --no-dev

# Install danloo-common in editable mode
RUN uv pip install -e ./common

# Install process project in editable mode
RUN uv pip install -e ./process

# ==========================================
# Stage 2: Runtime image (much smaller)
# ==========================================
FROM python:3.11-slim as runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /workspace

# Copy the virtual environment from builder stage
COPY --from=builder /workspace/.venv /workspace/.venv

# Copy source code
COPY --from=builder /workspace/common ./common/
COPY --from=builder /workspace/process ./process/

# Change ownership to non-root user
RUN chown -R appuser:appuser /workspace

# Switch to non-root user
USER appuser

# Set working directory to process service
WORKDIR /workspace/process

# Add virtual environment to PATH
ENV PATH="/workspace/.venv/bin:$PATH"
ENV PYTHONPATH="/workspace:$PYTHONPATH"

# Make entrypoint script executable if exists
RUN if [ -f entrypoint.sh ]; then chmod +x entrypoint.sh; fi

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Use entrypoint script if exists, otherwise uvicorn
CMD if [ -f entrypoint.sh ]; then ./entrypoint.sh; else python -m uvicorn main:app --host 0.0.0.0 --port 8001; fi

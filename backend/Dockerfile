# Multi-stage build optimized for both ARM64 (Apple Silicon) and AMD64 architectures

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install essential build dependencies
# Added support for ARM64 architecture
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with wheel building
# Using --platform=native to ensure architecture-specific wheels
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install packages from wheels
# This ensures we use the architecture-specific wheels built in the previous stage
RUN pip install --no-cache-dir --no-index --find-links=/app/wheels/ /app/wheels/* \
    && rm -rf /app/wheels

# Special handling for solc on ARM64
# This ensures py-solc-x can download and use the correct solc binary for the current architecture
RUN pip install --no-cache-dir py-solc-x && \
    python -c "from solcx import install_solc; install_solc(version='0.4.26')"

# Copy code
COPY . .

# Environment
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000

EXPOSE 8000

CMD ["flask", "run"]

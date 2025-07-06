# Base image Python slim
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including QEMU for x86_64 emulation on ARM
RUN apt-get update && apt-get install -y \
    build-essential gcc python3-dev curl git qemu-user-static \
    && rm -rf /var/lib/apt/lists/*

# Dependencies are installed via pip with binary packages
# No system-level build dependencies required

# Install py-solc-x and install solc compiler (version 0.4.26)
RUN pip install solc-select
RUN pip install --no-cache-dir py-solc-x && \
    python -c "from solcx import install_solc; install_solc(version='0.4.26')"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000

# Expose port
EXPOSE 8000

CMD ["gunicorn", "--timeout", "180", "-b", "0.0.0.0:8000", "app:app"]
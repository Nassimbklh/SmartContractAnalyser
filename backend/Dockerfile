# Multi-stage build for Python Flask backend

# Build stage
FROM python:3.9 AS build

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy installed packages from build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Expose port for the Flask application
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the application with Gunicorn
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
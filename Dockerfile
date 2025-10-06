# Production Dockerfile for Django Grant Management System
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.production.txt .
RUN pip install --no-cache-dir --user -r requirements.production.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings_production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user and group
RUN groupadd -r djf && useradd -r -g djf djf

# Create directories
RUN mkdir -p /app /var/log/djf /var/run/djf
RUN chown -R djf:djf /app /var/log/djf /var/run/djf

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/djf/.local

# Copy application code
COPY --chown=djf:djf . .

# Make sure scripts are executable
RUN chmod +x manage.py

# Switch to non-root user
USER djf

# Add local Python packages to PATH
ENV PATH=/home/djf/.local/bin:$PATH

# Collect static files
RUN python manage.py collectstatic --noinput --settings=core.settings_production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose port
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "core.wsgi:application", "-c", "gunicorn.conf.py"]
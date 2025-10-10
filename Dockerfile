# PostgreSQL Migration System

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs reports backups

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MIGRATION_LOG_LEVEL=INFO

# Expose ports for monitoring
EXPOSE 8080 9090

# Set executable permissions
RUN chmod +x activate-mcp.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "from core.monitor import health_check; health_check()" || exit 1

# Default command
CMD ["python3", "cli/run_migration.py", "--help"]

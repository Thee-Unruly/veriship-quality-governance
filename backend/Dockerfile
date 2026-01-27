FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js for Playwright
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    gnupg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Playwright server)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with dependencies
RUN playwright install --with-deps chromium firefox webkit

# Create directories for traces, screenshots, and videos
RUN mkdir -p /app/traces /app/screenshots /app/videos \
    && chmod 755 /app/traces /app/screenshots /app/videos

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application
CMD ["python", "run.py"]

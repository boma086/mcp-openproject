# Optimized Dockerfile for Smithery Deployment - Using confirmed Python version
FROM python:3.13.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Use Chinese mirrors for faster downloads
RUN sed -i 's@http://deb.debian.org@https://mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's@http://security.debian.org@https://mirrors.aliyun.com@g' /etc/apt/sources.list.d/debian.sources

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv

# Configure pip to use Chinese mirror
RUN /opt/venv/bin/pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    /opt/venv/bin/pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# Upgrade pip and install wheel
RUN /opt/venv/bin/pip install --upgrade pip wheel setuptools

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install dependencies in editable mode so the CLI is available
RUN /opt/venv/bin/pip install -e .

# Copy application files
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command for HTTP mode (Smithery deployment)
CMD ["mcp-openproject", "server", "--http", "--host", "0.0.0.0", "--port", "8000"]

# Labels for Smithery
LABEL maintainer="MCP OpenProject Team" \
      version="0.0.1" \
      description="MCP OpenProject Server with HTTP transport support"

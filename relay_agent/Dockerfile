# Use Python 3.11 Alpine for smaller image size
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for pyirsdk and native modules
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    build-base \
    linux-headers \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install pyirsdk with specific dependencies
RUN pip install --no-cache-dir pyirsdk

# Copy source code
COPY . .

# Create non-root user
RUN adduser -D -u 1001 blackbox

# Change ownership
RUN chown -R blackbox:blackbox /app
USER blackbox

# Expose port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', 8765))" || exit 1

# Start the relay agent
CMD ["python", "agent_main.py"]

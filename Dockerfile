# Multi-stage build for minimal image size and enhanced security
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root user for security
RUN groupadd -r botgroup && useradd -r -g botgroup botuser

# Copy installed python dependencies from builder
COPY --from=builder /root/.local /home/botuser/.local
ENV PATH=/home/botuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy source code
COPY app/ ./app/
COPY static/ ./static/
COPY run.py .

# Create persistent storage and logs directory with permissions
RUN mkdir -p data logs && chown -R botuser:botgroup /app

USER botuser

CMD ["python", "run.py"]

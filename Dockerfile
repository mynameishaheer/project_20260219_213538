FROM python:3.11-slim

WORKDIR /app

# System dependencies needed for psycopg2 (PostgreSQL) and Pillow (QR codes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x docker-entrypoint.sh

# SQLite database lives in a dedicated directory so it can be mounted as a volume
RUN mkdir -p /data

# Create non-root user and transfer ownership
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app /data

USER appuser

# DATABASE_URL defaults to the volume-mounted SQLite file.
# Override with a PostgreSQL URL for production:
#   DATABASE_URL=postgresql+psycopg2://user:pass@host/db
ENV DATABASE_URL="sqlite:////data/app.db" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Mount /data as a volume to persist the SQLite database across container restarts.
# For PostgreSQL deployments this volume is not needed.
VOLUME ["/data"]

ENTRYPOINT ["./docker-entrypoint.sh"]

# Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Manual Deployment](#manual-deployment)
4. [CI/CD Deployment](#cicd-deployment)
5. [Rollback](#rollback)
6. [Monitoring and Logs](#monitoring-and-logs)

---

## Prerequisites

| Requirement | Minimum version | Notes |
|---|---|---|
| Docker | 24.x | `docker --version` |
| Docker Compose | v2.x | bundled with Docker Desktop; or `docker compose version` |
| curl | any | used by health-check script |
| Bash | 4.x | scripts use `set -euo pipefail` |

All scripts live in `scripts/` and must be executable (see [Making scripts executable](#making-scripts-executable)).

---

## Environment Variables

Copy the example file and fill in the required values before the first deployment:

```bash
cp .env.example .env   # if an example file is provided
# or create .env manually
```

### Required

| Variable | Description |
|---|---|
| `SECRET_KEY` | Random string used for signing tokens / sessions |
| `DATABASE_URL` | Full database connection URL (see options below) |

### Database URL options

| Backend | Example value |
|---|---|
| SQLite (dev/local) | `sqlite:////data/app.db` |
| PostgreSQL (production) | `postgresql+psycopg2://user:pass@host:5432/dbname` |

### Optional

| Variable | Default | Description |
|---|---|---|
| `WORKERS` | `4` | Number of uvicorn worker processes |
| `DEBUG` | `false` | Enable debug mode (never use `true` in production) |
| `POSTGRES_DB` | `urlshortener` | PostgreSQL database name (prod compose only) |
| `POSTGRES_PASSWORD` | `password` | PostgreSQL password — **change this** |

---

## Manual Deployment

### Making scripts executable

Run once after cloning:

```bash
chmod +x scripts/deploy.sh scripts/rollback.sh scripts/health_check_app.sh scripts/migrate.sh
```

### Option A — Docker Compose (recommended for most deployments)

**Development / SQLite:**

```bash
docker compose up -d --build
```

**Production / PostgreSQL:**

```bash
# Export secrets (or put them in .env)
export POSTGRES_PASSWORD=changeme
export POSTGRES_DB=urlshortener

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The entrypoint automatically runs `alembic upgrade head` before starting uvicorn, so no separate migration step is needed on first start.

### Option B — Single-container deploy script

```bash
# Deploy latest build
./scripts/deploy.sh

# Deploy a specific image tag
./scripts/deploy.sh v1.2.3

# Deploy from a private registry
DOCKER_REGISTRY=ghcr.io/myorg ./scripts/deploy.sh v1.2.3
```

The script will:

1. Build the Docker image and tag it.
2. Run a smoke test against the new image.
3. Tag the currently-running image as `<app>:previous` (enables rollback).
4. Stop and remove the old container gracefully (30 s timeout).
5. Start the new container with `--restart unless-stopped`.
6. Verify the container is still running after 5 s.

### Verifying the deployment

```bash
# Container status
docker ps --filter name=project_20260219_213538

# Application health endpoint
./scripts/health_check_app.sh

# Or against a remote host
./scripts/health_check_app.sh https://your-domain.com
```

---

## CI/CD Deployment

### GitHub Actions example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build & push image
        run: |
          echo "${{ secrets.REGISTRY_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /opt/project_20260219_213538
            DOCKER_REGISTRY=ghcr.io/${{ github.repository_owner }} \
              ./scripts/deploy.sh ${{ github.sha }}
            ./scripts/health_check_app.sh

      - name: Notify on failure
        if: failure()
        run: echo "Deployment failed — check the Actions log and consider running rollback.sh"
```

### Required GitHub secrets

| Secret | Description |
|---|---|
| `DEPLOY_HOST` | IP or hostname of the target server |
| `DEPLOY_USER` | SSH user on the target server |
| `DEPLOY_SSH_KEY` | Private SSH key (the public key must be in `~/.ssh/authorized_keys` on the server) |
| `REGISTRY_TOKEN` | GitHub personal access token with `write:packages` scope |

---

## Rollback

### Application (Docker) rollback

Roll back to the image that was running before the last deployment:

```bash
./scripts/rollback.sh            # rolls back to :previous tag

./scripts/rollback.sh v1.1.0    # rolls back to a specific tag
```

The `deploy.sh` script automatically tags the previous image as `:previous` before each deployment, so `rollback.sh` (with no arguments) is the fastest recovery path.

### Database migration rollback

To undo the most recent Alembic migration:

```bash
./scripts/migrate.sh    # runs alembic downgrade -1
```

To downgrade to a specific revision:

```bash
docker exec project_20260219_213538 alembic downgrade <revision_id>
```

> **Important:** Always roll back the application code *before* rolling back the database schema, to avoid running old code against a newer schema.

---

## Monitoring and Logs

### Container logs

```bash
# Live tail
docker logs -f project_20260219_213538

# Last 100 lines
docker logs --tail 100 project_20260219_213538

# Logs since a specific time
docker logs --since 1h project_20260219_213538
```

### Health check endpoint

The application exposes `GET /health` which returns HTTP 200 when healthy.

```bash
# Quick check
curl http://localhost:8000/health

# Retry loop (useful in scripts / after deployment)
./scripts/health_check_app.sh [BASE_URL] [MAX_ATTEMPTS] [INTERVAL_SECS]
```

### Container resource usage

```bash
docker stats project_20260219_213538
```

### Database (PostgreSQL production)

```bash
# Connect to the database
docker exec -it db psql -U postgres -d urlshortener

# Check migration history
docker exec project_20260219_213538 alembic history
docker exec project_20260219_213538 alembic current
```

### Useful one-liners

```bash
# Restart the container without rebuilding
docker restart project_20260219_213538

# Open a shell inside the running container
docker exec -it project_20260219_213538 /bin/sh

# List all local image tags for this app
docker images project_20260219_213538
```

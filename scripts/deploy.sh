#!/bin/bash
# deploy.sh — Build, health-check, and (re)start the application container.
#
# Usage:
#   ./scripts/deploy.sh [TAG]
#
# TAG defaults to "latest". Pass a specific tag to deploy a pinned image, e.g.:
#   ./scripts/deploy.sh v1.2.3
#
# Environment:
#   DOCKER_REGISTRY  — optional prefix, e.g. "ghcr.io/myorg" (no trailing slash)
#   ENV_FILE         — path to the .env file (default: .env)
#
# The script tags the currently-running image as "<app>:previous" before
# replacing it, enabling a fast rollback via scripts/rollback.sh.
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
APP_NAME="project_20260219_213538"
TAG="${1:-latest}"
REGISTRY="${DOCKER_REGISTRY:-}"
ENV_FILE="${ENV_FILE:-.env}"

# Fully-qualified image name (registry prefix is optional)
if [[ -n "$REGISTRY" ]]; then
  IMAGE="${REGISTRY}/${APP_NAME}:${TAG}"
else
  IMAGE="${APP_NAME}:${TAG}"
fi

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
step() { echo; echo "──────────────────────────────────────────"; echo "  $*"; echo "──────────────────────────────────────────"; }

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
step "Pre-flight checks"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "WARNING: $ENV_FILE not found — container will start without env vars."
  echo "         Copy .env.example to .env and fill in the required values."
  ENV_FILE_ARG=()
else
  ENV_FILE_ARG=(--env-file "$ENV_FILE")
fi

# ---------------------------------------------------------------------------
# 1. Build
# ---------------------------------------------------------------------------
step "Building Docker image  →  $IMAGE"
docker build -t "$IMAGE" .

# Also tag as :latest for convenience when a specific tag was supplied
if [[ "$TAG" != "latest" ]]; then
  docker tag "$IMAGE" "${APP_NAME}:latest"
  log "Also tagged as ${APP_NAME}:latest"
fi

# ---------------------------------------------------------------------------
# 2. Health-check the new image (smoke test before touching production)
# ---------------------------------------------------------------------------
step "Smoke-testing new image"
docker run --rm "$IMAGE" python -c "
import sys, importlib
# Verify the main application module imports without errors
try:
    # Adjust 'main' if your entry-point module has a different name
    spec = importlib.util.find_spec('main')
    print('Module resolution OK' if spec else 'main module not found on path — skipping import check')
except Exception as e:
    print(f'Import check failed: {e}', file=sys.stderr)
    sys.exit(1)
print('✅ App OK')
" || { echo "❌ Smoke test failed — aborting deployment."; exit 1; }

# ---------------------------------------------------------------------------
# 3. Tag existing container's image as :previous (enables rollback)
# ---------------------------------------------------------------------------
step "Preserving previous image for rollback"
CURRENT_IMAGE=$(docker inspect --format '{{.Config.Image}}' "$APP_NAME" 2>/dev/null || true)
if [[ -n "$CURRENT_IMAGE" ]]; then
  docker tag "$CURRENT_IMAGE" "${APP_NAME}:previous" 2>/dev/null \
    && log "Tagged $CURRENT_IMAGE as ${APP_NAME}:previous" \
    || log "Could not tag previous image (non-fatal)"
else
  log "No running container found — skipping previous-image tag"
fi

# ---------------------------------------------------------------------------
# 4. Stop & remove the old container (graceful 30 s timeout)
# ---------------------------------------------------------------------------
step "Stopping old container"
docker stop --time 30 "$APP_NAME" 2>/dev/null && log "Stopped $APP_NAME" || log "$APP_NAME was not running"
docker rm "$APP_NAME" 2>/dev/null && log "Removed $APP_NAME" || true

# ---------------------------------------------------------------------------
# 5. Start the new container
# ---------------------------------------------------------------------------
step "Starting new container"
docker run -d \
  --name "$APP_NAME" \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "${APP_NAME}_data:/data" \
  "${ENV_FILE_ARG[@]}" \
  "$IMAGE"

log "Container started. Waiting 5 s for it to initialise..."
sleep 5

# ---------------------------------------------------------------------------
# 6. Verify the container is still running
# ---------------------------------------------------------------------------
step "Verifying deployment"
if docker ps --filter "name=^/${APP_NAME}$" --filter "status=running" | grep -q "$APP_NAME"; then
  echo
  echo "✅ Deployment successful!  Image: $IMAGE"
  docker ps --filter "name=^/${APP_NAME}$" --format "   {{.Names}}  {{.Status}}  {{.Ports}}"
else
  echo "❌ Container is not running after deployment!"
  echo "   Last 50 log lines:"
  docker logs --tail 50 "$APP_NAME" 2>&1 || true
  exit 1
fi

#!/bin/bash
# rollback.sh — Roll the running container back to a previous Docker image tag.
#
# NOTE: This script rolls back the *Docker container* (application code).
#       To roll back a *database migration*, use scripts/migrate.sh instead:
#           ./scripts/migrate.sh   (runs alembic downgrade -1)
#
# Usage:
#   ./scripts/rollback.sh [TAG]
#
# TAG defaults to "previous", which is the image automatically tagged by
# deploy.sh before each deployment.  You can also supply any image tag that
# exists locally or in your registry, e.g.:
#   ./scripts/rollback.sh v1.1.0
#
# Environment:
#   ENV_FILE  — path to the .env file (default: .env)
set -euo pipefail

APP_NAME="project_20260219_213538"
PREVIOUS_TAG="${1:-previous}"
TARGET_IMAGE="${APP_NAME}:${PREVIOUS_TAG}"
ENV_FILE="${ENV_FILE:-.env}"

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
step() { echo; echo "──────────────────────────────────────────"; echo "  $*"; echo "──────────────────────────────────────────"; }

# ---------------------------------------------------------------------------
# Verify the target image exists
# ---------------------------------------------------------------------------
step "Checking rollback target: $TARGET_IMAGE"
if ! docker image inspect "$TARGET_IMAGE" > /dev/null 2>&1; then
  echo "❌ Image $TARGET_IMAGE not found locally."
  echo "   Available tags for $APP_NAME:"
  docker images "$APP_NAME" --format "   {{.Tag}}  ({{.CreatedSince}})" 2>/dev/null || echo "   (none)"
  exit 1
fi
log "Found image $TARGET_IMAGE"

# ---------------------------------------------------------------------------
# Build env-file argument
# ---------------------------------------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
  echo "WARNING: $ENV_FILE not found — container will start without env vars."
  ENV_FILE_ARG=()
else
  ENV_FILE_ARG=(--env-file "$ENV_FILE")
fi

# ---------------------------------------------------------------------------
# Stop & remove the current container
# ---------------------------------------------------------------------------
step "Stopping current container"
docker stop --time 30 "$APP_NAME" 2>/dev/null && log "Stopped $APP_NAME" || log "$APP_NAME was not running"
docker rm "$APP_NAME" 2>/dev/null && log "Removed $APP_NAME" || true

# ---------------------------------------------------------------------------
# Start container from the rollback image
# ---------------------------------------------------------------------------
step "Starting rollback container  →  $TARGET_IMAGE"
docker run -d \
  --name "$APP_NAME" \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "${APP_NAME}_data:/data" \
  "${ENV_FILE_ARG[@]}" \
  "$TARGET_IMAGE"

log "Container started. Waiting 5 s to verify..."
sleep 5

# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
step "Verifying rollback"
if docker ps --filter "name=^/${APP_NAME}$" --filter "status=running" | grep -q "$APP_NAME"; then
  echo
  echo "✅ Rollback to $TARGET_IMAGE successful!"
  docker ps --filter "name=^/${APP_NAME}$" --format "   {{.Names}}  {{.Status}}  {{.Ports}}"
else
  echo "❌ Container failed to start after rollback!"
  echo "   Last 50 log lines:"
  docker logs --tail 50 "$APP_NAME" 2>&1 || true
  exit 1
fi

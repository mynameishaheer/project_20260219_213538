#!/bin/bash
# health_check_app.sh — Poll the application's /health endpoint until it
# responds successfully or the retry limit is reached.
#
# Usage:
#   ./scripts/health_check_app.sh [BASE_URL] [MAX_ATTEMPTS] [INTERVAL_SECONDS]
#
# Defaults:
#   BASE_URL        http://localhost:8000
#   MAX_ATTEMPTS    5
#   INTERVAL_SECS   5
#
# Exit codes:
#   0  — application is healthy
#   1  — application did not become healthy within the retry window
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
MAX_ATTEMPTS="${2:-5}"
INTERVAL="${3:-5}"

HEALTH_URL="${BASE_URL}/health"

echo "🔍 Checking ${HEALTH_URL} ..."
echo "   Max attempts : $MAX_ATTEMPTS"
echo "   Retry interval: ${INTERVAL}s"
echo

for i in $(seq 1 "$MAX_ATTEMPTS"); do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")

  if [[ "$HTTP_STATUS" == "200" ]]; then
    # Optionally print the response body for richer diagnostics
    BODY=$(curl -s --max-time 10 "$HEALTH_URL" 2>/dev/null || true)
    echo "✅ Application is healthy!  (HTTP $HTTP_STATUS)"
    [[ -n "$BODY" ]] && echo "   Response: $BODY"
    exit 0
  fi

  if [[ "$i" -lt "$MAX_ATTEMPTS" ]]; then
    echo "   Attempt $i/$MAX_ATTEMPTS — HTTP $HTTP_STATUS — not ready yet, waiting ${INTERVAL}s..."
    sleep "$INTERVAL"
  else
    echo "   Attempt $i/$MAX_ATTEMPTS — HTTP $HTTP_STATUS"
  fi
done

echo
echo "❌ Application health check failed after $MAX_ATTEMPTS attempts!"
echo "   Last status code: $HTTP_STATUS"
echo
echo "Troubleshooting hints:"
echo "  docker logs project_20260219_213538 --tail 50"
echo "  curl -v $HEALTH_URL"
exit 1

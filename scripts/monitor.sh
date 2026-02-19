#!/bin/bash
# monitor.sh — Continuously poll the /health endpoint and log results.
#
# Usage:
#   ./scripts/monitor.sh [APP_URL] [INTERVAL_SECONDS] [LOG_FILE]
#
# Defaults:
#   APP_URL          http://localhost:8000
#   INTERVAL_SECONDS 60
#   LOG_FILE         monitoring.log
#
# Press Ctrl+C to stop.

set -euo pipefail

APP_URL="${1:-http://localhost:8000}"
INTERVAL="${2:-60}"
LOG_FILE="${3:-monitoring.log}"

HEALTH_URL="${APP_URL}/health"

echo "Monitoring $HEALTH_URL every ${INTERVAL}s"
echo "Logging failures to: $LOG_FILE"
echo "Press Ctrl+C to stop."
echo

while true; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" \
    --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")

  if [ "$HTTP_STATUS" = "200" ]; then
    echo "[$TIMESTAMP] HEALTHY (HTTP $HTTP_STATUS)"
  else
    MSG="[$TIMESTAMP] UNHEALTHY (HTTP $HTTP_STATUS)"
    echo "$MSG"
    echo "$MSG" >> "$LOG_FILE"
  fi

  sleep "$INTERVAL"
done

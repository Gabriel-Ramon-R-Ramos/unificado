#!/usr/bin/env bash
set -euo pipefail

# check_after_deploy.sh
# Uso: ./check_after_deploy.sh [URL] [RETRIES]
# Exemplo: ./check_after_deploy.sh https://minha-api.app.aws 30

URL=${1:-http://localhost:8000/health}
RETRIES=${2:-30}
SLEEP=${3:-2}

echo "Checking health endpoint: $URL"

i=0
while [ $i -lt $RETRIES ]; do
  i=$((i+1))
  echo "Attempt $i/$RETRIES..."
  if curl -fsS --max-time 5 "$URL" -o /tmp/health.json; then
    echo "OK: endpoint returned:"
    cat /tmp/health.json
    rm -f /tmp/health.json
    exit 0
  else
    echo "Not ready yet, sleeping $SLEEP seconds"
    sleep $SLEEP
  fi
done

echo "Service did not become healthy after $RETRIES attempts"
exit 2

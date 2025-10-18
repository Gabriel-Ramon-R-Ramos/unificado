#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: run-build-step.sh <step-name> <command>" >&2
  exit 64
fi

STEP_NAME="$1"
shift
COMMAND="$1"

LOG_DIR="${BUILD_LOG_DIR:-/var/log/docker-build}"
mkdir -p "$LOG_DIR"

SAFE_STEP="$(echo "$STEP_NAME" | tr '[:upper:] ' '[:lower:]_' | tr -cd '[:alnum:]_')"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${TIMESTAMP}_${SAFE_STEP:-step}.log"

# Echo command execution with context to both stdout and log file.
{
  echo ">>> [${STEP_NAME}] $COMMAND"
  bash -o pipefail -c "$COMMAND"
} 2>&1 | tee "$LOG_FILE"
STATUS=${PIPESTATUS[0]}

if [ "$STATUS" -ne 0 ]; then
  echo "Step '${STEP_NAME}' failed with exit code $STATUS. Log: $LOG_FILE" >&2
  exit "$STATUS"
fi

exit 0
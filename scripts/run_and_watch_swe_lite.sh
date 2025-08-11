#!/usr/bin/env bash
set -euo pipefail

# Wrapper: start a SWE-bench Lite run and live-watch overall progress in this terminal.
# It calls scripts/run_swebench_lite.sh in the background, and refreshes the
# summary periodically using scripts/view_swebench_results.py.
#
# Usage:
#   scripts/run_and_watch_swe_lite.sh [--model sonnet4] [--max_tasks N] [--concurrency M]
#                                     [--run_id ID] [--refresh SECS] [--timeout_seconds T]
# Examples:
#   scripts/run_and_watch_swe_lite.sh --model sonnet4 --max_tasks 2
#   scripts/run_and_watch_swe_lite.sh --concurrency 6 --refresh 10

MODEL="sonnet4"
MAX_TASKS=0
CONCURRENCY=4
RUN_ID="swe-lite-$(date +%s)"
REFRESH=15
TIMEOUT_SECONDS=480

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --max_tasks) MAX_TASKS="$2"; shift 2 ;;
    --concurrency) CONCURRENCY="$2"; shift 2 ;;
    --run_id) RUN_ID="$2"; shift 2 ;;
    --refresh) REFRESH="$2"; shift 2 ;;
    --timeout_seconds) TIMEOUT_SECONDS="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--model sonnet4] [--max_tasks N] [--concurrency M] [--run_id ID] [--refresh SECS] [--timeout_seconds T]";
      exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Start the run in background; the runner will open a separate terminal/iTerm window to stream logs
"$ROOT_DIR/scripts/run_swebench_lite.sh" \
  --model "$MODEL" \
  --max_tasks "$MAX_TASKS" \
  --concurrency "$CONCURRENCY" \
  --run_id "$RUN_ID" \
  --timeout_seconds "$TIMEOUT_SECONDS" &
RUN_PID=$!

sleep 5

# Live summary loop
while true; do
  clear
  echo "Run ID: $RUN_ID"
  date
  if ! python3 "$ROOT_DIR/scripts/view_swebench_results.py" --run_id "$RUN_ID"; then
    echo "Waiting for first results..."
  fi

  # If the background run has exited, print one more summary and exit
  if ! kill -0 "$RUN_PID" >/dev/null 2>&1; then
    echo
    echo "Run process has exited. Final summary above (rerun viewer any time)."
    exit 0
  fi

  sleep "$REFRESH"
done


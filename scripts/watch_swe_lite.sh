#!/usr/bin/env bash
set -euo pipefail

# Watch-only script: reads files and shows live overall progress for a SWE-bench Lite run.
# It does NOT install anything or touch Docker. Purely reads results/ and logs/.
#
# Usage:
#   scripts/watch_swe_lite.sh [--run_id ID] [--refresh SECS] [--once] [--no-clear]
# Examples:
#   scripts/watch_swe_lite.sh                          # auto-detect latest run_id
#   scripts/watch_swe_lite.sh --run_id swe-lite-123    # watch a specific run
#   scripts/watch_swe_lite.sh --refresh 10             # update every 10s
#   scripts/watch_swe_lite.sh --once                   # print once and exit

RUN_ID=""
REFRESH=15
ONCE=0
NOCLEAR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run_id) RUN_ID="$2"; shift 2 ;;
    --refresh) REFRESH="$2"; shift 2 ;;
    --once) ONCE=1; shift 1 ;;
    --no-clear) NOCLEAR=1; shift 1 ;;
    -h|--help)
      echo "Usage: $0 [--run_id ID] [--refresh SECS] [--once] [--no-clear]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Auto-detect latest run_id if not provided
if [[ -z "$RUN_ID" ]]; then
  if ls -1dt "$ROOT_DIR"/results/swe-lite-* >/dev/null 2>&1; then
    RUN_ID=$(ls -1dt "$ROOT_DIR"/results/swe-lite-* | head -n1 | xargs -n1 basename)
  else
    echo "No results/swe-lite-* runs found."
    exit 1
  fi
fi

watch_once() {
  [[ "$NOCLEAR" -eq 1 ]] || clear
  echo "Run ID: $RUN_ID"
  date
  if ! python3 "$ROOT_DIR/scripts/view_swebench_results.py" --run_id "$RUN_ID"; then
    echo "Waiting for first results..."
  fi
}

watch_loop() {
  while true; do
    watch_once
    sleep "$REFRESH"
  done
}

if [[ "$ONCE" -eq 1 ]]; then
  watch_once
else
  watch_loop
fi


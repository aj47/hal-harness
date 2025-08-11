#!/usr/bin/env bash
set -euo pipefail

# One-command runner for SWE-bench Lite with Auggie (Sonnet 4) on macOS
# - Installs micromamba if missing
# - Creates conda env swebench_hal and installs swebench harness
# - Verifies Docker Desktop is running and sets DOCKER_HOST if needed
# - Generates predictions with Auggie
# - Runs evaluation with streaming logs in a new Terminal window
# - Persists all logs under results/<RUN_ID>

# Usage:
#   scripts/run_swebench_lite.sh [--model sonnet4] [--max_tasks N] [--concurrency M]
#                                [--run_id ID] [--start_index K] [--timeout_seconds T]
# Example:
#   scripts/run_swebench_lite.sh --model sonnet4 --max_tasks 5

MODEL="sonnet4"
MAX_TASKS=0
CONCURRENCY=4
RUN_ID="swe-lite-$(date +%Y%m%d-%H%M%S)"
START_INDEX=0
TIMEOUT_SECONDS=480

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --max_tasks) MAX_TASKS="$2"; shift 2 ;;
    --concurrency) CONCURRENCY="$2"; shift 2 ;;
    --run_id) RUN_ID="$2"; shift 2 ;;
    --start_index) START_INDEX="$2"; shift 2 ;;
    --timeout_seconds) TIMEOUT_SECONDS="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESULTS_DIR="$ROOT_DIR/results/$RUN_ID"
LOG_DIR="$RESULTS_DIR/logs"
PRED_PATH="$RESULTS_DIR/${RUN_ID}_SWE_BENCH_SUBMISSIONS.jsonl"
EVAL_JSON="$RESULTS_DIR/evaluation.json"

mkdir -p "$LOG_DIR"

# Prepare tailer to stream logs in another terminal before generation starts
TAIL_SCRIPT="$RESULTS_DIR/tail_logs.sh"
cat > "$TAIL_SCRIPT" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
RUN_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$(cd "$RUN_DIR/.." && pwd)"
LOG_DIR="$RESULTS_DIR/logs"
# REPO_ROOT is injected by parent script below
REPO_ROOT_PLACEHOLDER
# Ensure log files exist so tail -F glob doesn't fail
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/generate.log" "$LOG_DIR/eval.log"
(
  echo "=== Streaming generate.log and eval.log ==="
  tail -n +1 -F "$LOG_DIR"/generate.log "$LOG_DIR"/eval.log &
  # Also stream any Auggie per-task logs if present under results dir (if copied)
  find "$RESULTS_DIR" -type f -name 'auggie_*.txt' -print0 | while IFS= read -r -d '' f; do
    echo "=== $f ==="
    tail -n +1 -F "$f" &
  done
  # Stream harness logs under repo logs/ as they are created
  if [[ -d "$REPO_ROOT/logs" ]]; then
    echo "=== Streaming harness logs under $REPO_ROOT/logs ==="
    find "$REPO_ROOT/logs" -type f -name '*.log' -print0 | while IFS= read -r -d '' f; do
      echo "=== $f ==="
      tail -n +1 -F "$f" &
    done
  fi
  wait
)
EOS
# Inject actual REPO_ROOT path and make executable
sed -i '' "s|REPO_ROOT_PLACEHOLDER|REPO_ROOT=\"$ROOT_DIR\"|" "$TAIL_SCRIPT"
chmod +x "$TAIL_SCRIPT"

# Open tailer window now
open -a "iTerm" "$TAIL_SCRIPT" 2>/dev/null || open -a "Terminal" "$TAIL_SCRIPT" 2>/dev/null || true

info() { echo "[$(date +%Y-%m-%dT%H:%M:%S)] $*"; }

# 0) Check requirements: Docker Desktop
if ! command -v docker >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    info "Docker CLI not found. Installing Docker Desktop via Homebrew Cask..."
    brew install --cask docker || {
      info "Failed to install Docker Desktop via Homebrew. Please install manually from https://www.docker.com/products/docker-desktop/"; exit 1;
    }
    open -a Docker || true
    info "Waiting for Docker Desktop to start..."
    for i in {1..60}; do
      if docker info >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done
  else
    info "Docker not found and Homebrew is not installed. Please install Docker Desktop manually."; exit 1
  fi
fi

# Ensure Docker engine is reachable
if ! docker info >/dev/null 2>&1; then
  info "Docker not reachable. Ensure Docker Desktop is running."
  # Try common macOS socket path override
  if [[ -S "$HOME/.docker/run/docker.sock" ]]; then
    export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
    info "Set DOCKER_HOST=$DOCKER_HOST"
  fi
  if ! docker info >/dev/null 2>&1; then
    info "Please start Docker Desktop, then re-run this script."; exit 1
  fi
fi

# 1) Ensure micromamba (fast conda) for isolated env
if ! command -v micromamba >/dev/null 2>&1; then
  info "Installing micromamba..."
  curl -L https://micro.mamba.pm/api/micromamba/osx-64/latest | tar -xj bin/micromamba
  MAMBA_BIN="$ROOT_DIR/bin/micromamba"
  mkdir -p "$ROOT_DIR/bin"
  mv bin/micromamba "$MAMBA_BIN"
else
  MAMBA_BIN="$(command -v micromamba)"
fi

# 2) Create env and install swebench harness
ENV_NAME="swebench_hal"
"$MAMBA_BIN" create -y -q -n "$ENV_NAME" python=3.11 || true

# We install/upgrade pip packages inside the env using micromamba run to avoid path issues
info "Installing swebench harness in $ENV_NAME ..."
"$MAMBA_BIN" run -n "$ENV_NAME" python -m pip install -U pip
"$MAMBA_BIN" run -n "$ENV_NAME" python -m pip install -U -e git+https://github.com/benediktstroebl/SWE-bench.git#egg=swebench

# 3) Ensure Auggie is installed
if ! command -v auggie >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    info "Installing Auggie via Homebrew..."
    brew install augmentcode/auggie/auggie || {
      info "Failed to install Auggie via Homebrew. Please install manually and run 'auggie --login'."; exit 1;
    }
  else
    info "Auggie CLI not found and Homebrew is not installed. Please install Homebrew (https://brew.sh) and run: brew install augmentcode/auggie/auggie"
    exit 1
  fi
fi

# 4) Install Python deps for generation and generate predictions (Lite)
info "Ensuring Python deps in $ENV_NAME ..."
"$MAMBA_BIN" run -n "$ENV_NAME" python -m pip install -U datasets

info "Generating predictions to $PRED_PATH ..."
(
  export PYTHONUNBUFFERED=1
  "$MAMBA_BIN" run -n "$ENV_NAME" python "$ROOT_DIR/scripts/generate_swe_lite_predictions.py" \
    --model "$MODEL" \
    --out "$PRED_PATH" \
    --max_tasks "$MAX_TASKS" \
    --start_index "$START_INDEX" \
    --timeout_seconds "$TIMEOUT_SECONDS" \
    2>&1 | tee "$LOG_DIR/generate.log"
)

# 5) Run evaluation in env, stream logs in new Terminal
EVAL_CMD=("$MAMBA_BIN" run -n "$ENV_NAME" python -m swebench.harness.run_evaluation \
  --dataset_name princeton-nlp/SWE-bench_Lite \
  --predictions_path "$PRED_PATH" \
  --max_workers "$CONCURRENCY" \
  --run_id "$RUN_ID")

info "Starting evaluation... logs will stream to a new Terminal window."

# macOS Terminal new window tail
EVAL_LOG="$LOG_DIR/eval.log"
RUN_CMD_FILE="$RESULTS_DIR/RUN_COMMAND.txt"

printf "%q " "${EVAL_CMD[@]}" > "$RUN_CMD_FILE"

# Start eval in background and tee logs
(
  set -o pipefail
  "${EVAL_CMD[@]}" 2>&1 | tee "$EVAL_LOG"
) &
EVAL_PID=$!

# Open another terminal window to live-tail all logs
# Prefer iTerm2 if available, else use Apple Terminal
TAIL_SCRIPT="$RESULTS_DIR/tail_logs.sh"
cat > "$TAIL_SCRIPT" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
RUN_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$(cd "$RUN_DIR/.." && pwd)"
LOG_DIR="$RESULTS_DIR/logs"
# REPO_ROOT is injected by parent script below
REPO_ROOT_PLACEHOLDER
(
  echo "=== Streaming generate.log and eval.log ==="
  tail -n +1 -F "$LOG_DIR"/*.log &
  # Also stream any Auggie per-task logs if present
  find "$RESULTS_DIR" -type f -name 'auggie_*.txt' -print0 | while IFS= read -r -d '' f; do
    echo "=== $f ==="
    tail -n +1 -F "$f" &
  done
  # Stream harness logs under repo logs/ as they are created
  if [[ -d "$REPO_ROOT/logs" ]]; then
    echo "=== Streaming harness logs under $REPO_ROOT/logs ==="
    find "$REPO_ROOT/logs" -type f -name '*.log' -print0 | while IFS= read -r -d '' f; do
      echo "=== $f ==="
      tail -n +1 -F "$f" &
    done
  fi
  wait
)
EOS
# Inject actual REPO_ROOT path
sed -i '' "s|REPO_ROOT_PLACEHOLDER|REPO_ROOT=\"$ROOT_DIR\"|" "$TAIL_SCRIPT"
chmod +x "$TAIL_SCRIPT"

open -a "iTerm" "$TAIL_SCRIPT" 2>/dev/null || open -a "Terminal" "$TAIL_SCRIPT" 2>/dev/null || true

# Wait for evaluation to finish
wait $EVAL_PID || true

# 6) Gather final results into $EVAL_JSON if produced in CWD by harness
# The harness writes *.<run_id>.json in CWD; move the first match
CAND=$(ls -1 *."$RUN_ID".json 2>/dev/null | head -n1 || true)
if [[ -n "${CAND:-}" && -f "$CAND" ]]; then
  mv "$CAND" "$EVAL_JSON"
  info "Final evaluation JSON saved to $EVAL_JSON"
else
  info "Could not locate evaluation JSON. Check logs in $LOG_DIR and repo logs/."
fi

info "Run complete. Results under $RESULTS_DIR"


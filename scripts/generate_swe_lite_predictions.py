#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from typing import Dict, Any

# Ensure repo root on path for module imports
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from datasets import load_dataset  # type: ignore
from agents.auggie_swebench.main import run as auggie_run  # type: ignore


def flush(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Generate SWE-bench Lite predictions with Auggie")
    parser.add_argument("--model", "--model_name", dest="model", default="sonnet4", help="Auggie model name (e.g., sonnet4)")
    parser.add_argument("--out", required=True, help="Output JSONL path for predictions")
    parser.add_argument("--max_tasks", type=int, default=0, help="Limit number of tasks (0 = all)")
    parser.add_argument("--start_index", type=int, default=0, help="Start from this index in the dataset")
    parser.add_argument("--timeout_seconds", type=int, default=480, help="Per-task Auggie timeout in seconds")

    args = parser.parse_args()

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    flush("Loading SWE-bench Lite dataset (test split)...")
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

    total = len(ds)
    start = max(0, args.start_index)
    end = total if args.max_tasks in (None, 0) else min(total, start + args.max_tasks)
    flush(f"Dataset size: {total}. Processing indices [{start}:{end}) ...")

    # Open output file
    written = 0
    with open(args.out, "w") as f:
        for idx in range(start, end):
            rec: Dict[str, Any] = ds[idx]
            instance_id = rec.get("instance_id")
            problem_statement = (rec.get("problem_statement") or rec.get("problem_statement_str") or "").strip()
            repo = (rec.get("repo") or rec.get("repo_full_name") or "").strip()
            base_commit = (rec.get("base_commit") or "").strip()
            env_setup_commit = (rec.get("environment_setup_commit") or "").strip()

            if not instance_id:
                flush(f"Skipping index {idx}: missing instance_id")
                continue

            input_data = {
                instance_id: {
                    "problem_statement": problem_statement,
                    "repo": repo,
                    "base_commit": base_commit,
                    "environment_setup_commit": env_setup_commit,
                }
            }

            flush(f"[{written+1}] Running Auggie on {instance_id} ({repo}@{base_commit[:7]}) ...")
            try:
                result_map = auggie_run(input_data, model_name=args.model, timeout_seconds=args.timeout_seconds)
            except Exception as e:
                flush(f"ERROR running Auggie for {instance_id}: {e}")
                result_map = {instance_id: f"ERROR: {e}"}

            # If the agent created local logs in its temp workdir, copy them alongside results for tailing
            # The agent writes auggie_stdout.txt/auggie_stderr.txt inside its temp workspace, but it cleans up after.
            # So live streaming happens via stdout; here we do nothing extra.

            model_patch = result_map.get(instance_id, "ERROR: No output from Auggie")

            out_obj = {
                "instance_id": instance_id,
                "model_patch": model_patch,
                "model_name_or_path": f"Auggie({args.model})",
            }
            f.write(json.dumps(out_obj) + "\n")
            f.flush()
            written += 1
            flush(f"[{written}] Wrote prediction for {instance_id}")

    flush(f"Done. Wrote {written} predictions to {args.out}")


if __name__ == "__main__":
    main()


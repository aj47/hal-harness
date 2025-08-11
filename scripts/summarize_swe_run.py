#!/usr/bin/env python3
"""
Summarize SWE-bench run pass/fail counts using simple file reads.

It aggregates per-instance report.json files that the harness writes under:
  logs/run_evaluation/<run_id>/**/report.json

Each report.json is expected to be a dict with a single key (instance_id)
whose value contains a field "resolved": True/False.

Usage examples:
  # Summarize a specific run
  python3 scripts/summarize_swe_run.py --run_id swe-lite-20250809-161802

  # List all runs found under logs/run_evaluation and summarize each
  python3 scripts/summarize_swe_run.py --all

Optional:
  --json  Print the summary JSON for the run (when using --run_id)
  --top N Show up to N IDs for each of resolved/failed/unknown (default 10)

This script performs only local file reads (no Docker, no network operations).
"""

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Tuple


def find_report_files_for_run(run_id: str) -> List[str]:
    base = os.path.join("logs", "run_evaluation", run_id)
    if not os.path.isdir(base):
        return []
    return glob.glob(os.path.join(base, "**", "report.json"), recursive=True)


def summarize_from_reports(report_files: List[str]) -> Dict[str, Any]:
    resolved = 0
    failed = 0
    unknown = 0
    resolved_ids: List[str] = []
    failed_ids: List[str] = []
    unknown_ids: List[str] = []

    for fp in report_files:
        try:
            with open(fp, "r") as f:
                data = json.load(f)
            # Expect a dict with a single key = instance_id
            if not isinstance(data, dict) or not data:
                unknown += 1
                unknown_ids.append(f"<malformed:{os.path.basename(fp)}>")
                continue
            instance_id, report = list(data.items())[0]
            val = None
            if isinstance(report, dict):
                val = report.get("resolved")
            if val is True:
                resolved += 1
                resolved_ids.append(instance_id)
            elif val is False:
                failed += 1
                failed_ids.append(instance_id)
            else:
                unknown += 1
                unknown_ids.append(instance_id)
        except Exception:
            unknown += 1
            unknown_ids.append(f"<error:{os.path.basename(fp)}>")

    summary = {
        "total_instances": len(report_files),
        "resolved_instances": resolved,
        "unresolved_instances": failed,
        "unknown_instances": unknown,
        "resolved_ids": resolved_ids,
        "unresolved_ids": failed_ids,
        "error_ids": unknown_ids,
    }
    return summary


def print_human_summary(run_id: str, summary: Dict[str, Any], top: int) -> None:
    total = int(summary.get("total_instances", 0))
    resolved = int(summary.get("resolved_instances", 0))
    unresolved = int(summary.get("unresolved_instances", 0))
    unknown = int(summary.get("unknown_instances", 0))
    acc = (resolved / total) if total else 0.0

    print(f"\nSWE-bench Results for run_id={run_id}")
    print("-" * 60)
    print(f"Total instances:   {total}")
    print(f"Resolved (passed): {resolved}")
    print(f"Unresolved:        {unresolved}")
    print(f"Unknown/Error:     {unknown}")
    print(f"Accuracy:          {acc:.2%}")

    def _print_section(title: str, ids: List[str]):
        print(f"\n{title} ({len(ids)}):")
        for iid in ids[:top]:
            print(f"  - {iid}")
        if len(ids) > top:
            print(f"  ... (+{len(ids) - top} more)")

    _print_section("Resolved IDs", list(summary.get("resolved_ids", [])))
    _print_section("Unresolved IDs", list(summary.get("unresolved_ids", [])))
    _print_section("Unknown/Error IDs", list(summary.get("error_ids", [])))


def summarize_run(run_id: str) -> Tuple[Dict[str, Any], List[str]]:
    files = find_report_files_for_run(run_id)
    return summarize_from_reports(files), files


def list_runs_under_logs() -> List[str]:
    base = os.path.join("logs", "run_evaluation")
    if not os.path.isdir(base):
        return []
    return sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))])


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize SWE-bench run pass/fail counts")
    p.add_argument("--run_id", help="Run ID under logs/run_evaluation to summarize")
    p.add_argument("--all", action="store_true", help="Summarize all runs under logs/run_evaluation")
    p.add_argument("--json", action="store_true", help="Print full summary JSON (only with --run_id)")
    p.add_argument("--top", type=int, default=10, help="How many IDs to show per section")
    args = p.parse_args()

    if args.all:
        runs = list_runs_under_logs()
        if not runs:
            print("No runs found under logs/run_evaluation")
            return
        rows: List[Tuple[str, int, int, int, int]] = []
        for run_id in runs:
            summary, _ = summarize_run(run_id)
            rows.append(
                (
                    run_id,
                    int(summary.get("total_instances", 0)),
                    int(summary.get("resolved_instances", 0)),
                    int(summary.get("unresolved_instances", 0)),
                    int(summary.get("unknown_instances", 0)),
                )
            )
        # Pretty print table
        print(f"{'run_id':60}  total  passed  failed  unknown")
        for run_id, total, passed, failed, unknown in sorted(rows, key=lambda r: r[1], reverse=True):
            print(f"{run_id:60}  {total:5d}  {passed:6d}  {failed:6d}  {unknown:7d}")
        return

    if not args.run_id:
        print("Please specify --run_id or use --all to summarize all runs.")
        return

    summary, files = summarize_run(args.run_id)
    if not files:
        print(f"No report.json files found for run_id={args.run_id} under logs/run_evaluation/{args.run_id}")
        return

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_human_summary(args.run_id, summary, args.top)


if __name__ == "__main__":
    main()


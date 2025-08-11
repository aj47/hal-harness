#!/usr/bin/env python3
import argparse
import json
import os
import sys
import glob
from typing import Dict, Any, List, Tuple, Set

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_final_report(run_id: str, explicit_path: str | None) -> Tuple[Dict[str, Any] | None, str | None]:
    """Try to load the final evaluation report JSON for a run.
    Returns (report_dict, path_used) or (None, None) if not found.
    """
    candidates: List[str] = []

    if explicit_path:
        candidates.append(explicit_path)

    # results/<run_id>/evaluation.json (our runner's canonical location)
    candidates.append(os.path.join(REPO_ROOT, "results", run_id, "evaluation.json"))

    # <model>.<run_id>.json in repo root (harness default)
    candidates.extend(glob.glob(os.path.join(REPO_ROOT, f"*.{run_id}.json")))

    for path in candidates:
        if path and os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                return data, path
            except Exception:
                continue

    return None, None


essential_keys = {
    "resolved_instances",
    "total_instances",
    "resolved_ids",
    "unresolved_ids",
    "error_ids",
}


def aggregate_from_reports(run_id: str) -> Tuple[Dict[str, Any] | None, str | None]:
    """Aggregate per-instance report.json files into a summary similar to harness output.
    Returns (report_dict, source_dir) or (None, None) if not available.
    """
    base = os.path.join(REPO_ROOT, "logs", "run_evaluation", run_id)
    if not os.path.isdir(base):
        return None, None

    # Find all report.json files under run_id/*/*/report.json
    report_files = glob.glob(os.path.join(base, "**", "report.json"), recursive=True)
    if not report_files:
        return None, base

    resolved_ids: Set[str] = set()
    unresolved_ids: Set[str] = set()
    error_ids: Set[str] = set()

    for report_path in report_files:
        try:
            with open(report_path, "r") as f:
                per = json.load(f)
            # per is {instance_id: {...}} per harness
            if not isinstance(per, dict) or not per:
                continue
            (iid, data), = per.items()
            resolved = bool(data.get("resolved"))
            if resolved:
                resolved_ids.add(iid)
            else:
                # Treat missing or False resolved as unresolved, unless error present
                if data.get("error") or data.get("exception"):
                    error_ids.add(iid)
                else:
                    unresolved_ids.add(iid)
        except Exception:
            continue

    # Avoid double-counting: remove errors from unresolved
    unresolved_ids -= error_ids

    summary = {
        "resolved_instances": len(resolved_ids),
        "total_instances": len(resolved_ids) + len(unresolved_ids) + len(error_ids),
        "resolved_ids": sorted(resolved_ids),
        "unresolved_ids": sorted(unresolved_ids),
        "error_ids": sorted(error_ids),
        "schema_version": 2,
        "source": f"aggregated-from:{base}",
    }
    return summary, base


def print_human_summary(report: Dict[str, Any], run_id: str, source: str | None, top: int):
    total = int(report.get("total_instances", 0))
    resolved = int(report.get("resolved_instances", 0))
    unresolved_ids = list(report.get("unresolved_ids", []))
    resolved_ids = list(report.get("resolved_ids", []))
    error_ids = list(report.get("error_ids", []))

    acc = (resolved / total) if total else 0.0

    print(f"\nSWE-bench Results for run_id={run_id}")
    if source:
        print(f"Source: {source}")
    print("-" * 60)
    print(f"Total instances:   {total}")
    print(f"Resolved:          {resolved}")
    print(f"Errors:            {len(error_ids)}")
    print(f"Unresolved:        {len(unresolved_ids)}")
    print(f"Accuracy:          {acc:.2%}")

    if resolved_ids:
        print("\nResolved IDs (sample):")
        for iid in resolved_ids[:top]:
            print(f"  - {iid}")
        if len(resolved_ids) > top:
            print(f"  (+{len(resolved_ids) - top} more)")

    if error_ids:
        print("\nError IDs (sample):")
        for iid in error_ids[:top]:
            print(f"  - {iid}")
        if len(error_ids) > top:
            print(f"  (+{len(error_ids) - top} more)")

    if unresolved_ids:
        print("\nUnresolved IDs (sample):")
        for iid in unresolved_ids[:top]:
            print(f"  - {iid}")
        if len(unresolved_ids) > top:
            print(f"  (+{len(unresolved_ids) - top} more)")
    print()


def main():
    p = argparse.ArgumentParser(description="View overall results for a SWE-bench run")
    p.add_argument("--run_id", required=True, help="Run ID (directory under results/) to summarize")
    p.add_argument("--path", help="Explicit path to final report JSON (overrides auto-detect)")
    p.add_argument("--json", action="store_true", help="Print the full summary JSON")
    p.add_argument("--top", type=int, default=10, help="How many IDs to show per section")
    args = p.parse_args()

    report, src = load_final_report(args.run_id, args.path)
    if report is None:
        report, src = aggregate_from_reports(args.run_id)

    if report is None:
        print(f"Could not find results for run_id={args.run_id}.\nTried results/{args.run_id}/evaluation.json, *.{args.run_id}.json, and logs/run_evaluation/{args.run_id}/**/report.json.")
        sys.exit(1)

    # If this is a harness final report, it has the field set we expect.
    # If aggregated, we built a compatible subset.
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human_summary(report, args.run_id, src, args.top)


if __name__ == "__main__":
    main()


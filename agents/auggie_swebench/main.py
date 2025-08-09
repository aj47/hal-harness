import json
import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any


def run(input_data: Dict[str, Any], **kwargs) -> Dict[str, str]:
    """
    Auggie wrapper for HAL harness (SWE-bench) that:
    - Clones the target repo at the base commit into a temp git workspace
    - Runs Auggie with that workspace so it can apply code changes
    - Exports a patch by running `git diff` and returns it as the submission

    Expects input_data: { instance_id: { problem_statement, repo, base_commit, environment_setup_commit } }
    Returns: { instance_id: unified_diff_patch_string }
    """
    workdir = None
    try:
        # Expect a single instance
        if not isinstance(input_data, dict) or len(input_data) == 0:
            return {"ERROR": "Invalid input_data; expected a non-empty dict"}

        (instance_id, data), = input_data.items()
        problem_statement = data.get("problem_statement", "").strip()
        repo = data.get("repo", "").strip()  # e.g., "django/django"
        base_commit = data.get("base_commit", "").strip()
        env_setup_commit = data.get("environment_setup_commit", "").strip()

        # Optional agent args - supports all Auggie models including Claude Sonnet 4 (sonnet4)
        model = kwargs.get("model_name") or kwargs.get("model")

        # 1) Prepare a temporary git workspace for Auggie
        workdir = tempfile.mkdtemp(prefix="auggie-swebench-")
        repo_url = f"https://github.com/{repo}.git"

        git_env = os.environ.copy()
        # Make git non-interactive and set a default identity (needed for staging)
        git_env.setdefault("GIT_TERMINAL_PROMPT", "0")

        def run_cmd(cmd, cwd=None, check=True):
            return subprocess.run(cmd, cwd=cwd, env=git_env, text=True, capture_output=True, check=check)

        # Clone and checkout base commit
        run_cmd(["git", "init"], cwd=workdir)
        run_cmd(["git", "remote", "add", "origin", repo_url], cwd=workdir)
        # Shallow fetch of the base commit and checkout
        run_cmd(["git", "fetch", "--depth", "1", "origin", base_commit], cwd=workdir)
        run_cmd(["git", "checkout", "FETCH_HEAD"], cwd=workdir)
        # Set minimal user for staging
        run_cmd(["git", "config", "user.email", "auggie@example.com"], cwd=workdir)
        run_cmd(["git", "config", "user.name", "Auggie"], cwd=workdir)

        # 2) Ask Auggie to apply the fix to the checked-out workspace
        instruction = (
            "You are participating in a SWE-bench-style patch generation task.\n"
            "Apply the minimal code changes to resolve the issue in this repository checkout.\n"
            "Do not print a diff. Do not include explanations.\n\n"
            f"Repository: {repo}\n"
            f"Base commit: {base_commit}\n"
            f"Environment setup commit: {env_setup_commit}\n\n"
            "Issue / Problem Statement (verbatim):\n"
            f"{problem_statement}\n\n"
            "Constraints:\n"
            "- Modify files directly under the workspace root only as needed.\n"
            "- Avoid formatting-only changes.\n"
        )
        # Run Auggie in non-interactive mode but operate on the workspace files
        # We still rely on git diff for the actual patch, so we ignore stdout.
        cmd = [
            "auggie",
            "--workspace-root", workdir,
            "--dont-save-session",
            "--print",
            instruction,
        ]
        if model:
            cmd += ["--model", str(model)]
        timeout_s = int(kwargs.get("timeout_seconds", 480))
        try:
            proc = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {instance_id: "ERROR: Auggie timed out"}
        # Persist auggie stdout/stderr for debugging
        with open(os.path.join(workdir, "auggie_stdout.txt"), "w") as _f:
            _f.write(proc.stdout or "")
        with open(os.path.join(workdir, "auggie_stderr.txt"), "w") as _f:
            _f.write(proc.stderr or "")
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "Auggie failed").strip()
            return {instance_id: f"ERROR: {err}"}

        # 3) Produce a unified diff of changes
        # Stage all changes (include new/deleted files), then diff from index
        run_cmd(["git", "add", "-A"], cwd=workdir)
        diff = run_cmd(["git", "diff", "--cached"], cwd=workdir, check=False).stdout
        diff = (diff or "").strip()
        if not diff:
            return {instance_id: "ERROR: No changes detected (empty diff)"}

        # Also write patch to a file in the workspace for debugging
        patch_path = os.path.join(workdir, f"{instance_id}.patch")
        with open(patch_path, "w") as f:
            f.write(diff if diff.endswith("\n") else diff + "\n")

        return {instance_id: diff if diff.endswith("\n") else diff + "\n"}

    except Exception as e:
        try:
            (instance_id, _), = input_data.items()
        except Exception:
            instance_id = "UNKNOWN_INSTANCE"
        return {instance_id: f"ERROR: {str(e)}"}
    finally:
        # Clean up workspace
        if workdir and os.path.isdir(workdir):
            shutil.rmtree(workdir, ignore_errors=True)


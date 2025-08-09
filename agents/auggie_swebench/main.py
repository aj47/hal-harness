import json
import subprocess
from typing import Dict, Any


def run(input_data: Dict[str, Any], **kwargs) -> Dict[str, str]:
    """
    Minimal Auggie wrapper for HAL harness (SWE-bench).

    Expects input_data to be a mapping: { instance_id: { problem_statement, repo, base_commit, environment_setup_commit } }
    Returns: { instance_id: unified_diff_patch_string }
    """
    try:
        # Expect a single instance
        if not isinstance(input_data, dict) or len(input_data) == 0:
            return {"ERROR": "Invalid input_data; expected a non-empty dict"}

        (instance_id, data), = input_data.items()
        problem_statement = data.get("problem_statement", "").strip()
        repo = data.get("repo", "").strip()
        base_commit = data.get("base_commit", "").strip()
        env_setup_commit = data.get("environment_setup_commit", "").strip()

        # Optional: allow passing a model via -A model_name=...
        model = kwargs.get("model_name") or kwargs.get("model")

        # Build a succinct instruction for Auggie.
        # Ask strictly for a unified diff patch with no extra commentary or code fences.
        instruction = (
            "You are participating in a SWE-bench-style patch generation task.\n"
            "Given a repository and base commit, generate a minimal unified diff patch that resolves the issue.\n\n"
            f"Repository: {repo}\n"
            f"Base commit: {base_commit}\n"
            f"Environment setup commit: {env_setup_commit}\n\n"
            "Issue / Problem Statement (verbatim):\n"
            f"{problem_statement}\n\n"
            "Requirements:\n"
            "- Output ONLY a valid unified diff (patch) with correct file paths relative to repo root.\n"
            "- Do not include any prose, explanations, or code fences.\n"
            "- The patch must apply cleanly to the specified base commit.\n"
        )

        cmd = ["auggie", "--print", instruction]
        if model:
            cmd += ["--model", str(model)]

        # Execute Auggie in print mode to get the patch as plain text
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if proc.returncode != 0:
            err = (proc.stderr or "Auggie failed").strip()
            return {instance_id: f"ERROR: {err}"}

        output = (proc.stdout or "").strip()
        if not output:
            return {instance_id: "ERROR: Empty output from Auggie"}

        # Return the patch as-is
        return {instance_id: output}

    except Exception as e:
        # Fall back to returning an error for this instance
        try:
            (instance_id, _), = input_data.items()  # best-effort extract
        except Exception:
            instance_id = "UNKNOWN_INSTANCE"
        return {instance_id: f"ERROR: {str(e)}"}


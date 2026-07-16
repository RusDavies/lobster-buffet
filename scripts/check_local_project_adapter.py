#!/usr/bin/env python3
"""Regression checks for the local project command adapter."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def run_json(command: list[str], env: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    return json.loads(completed.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp) / "clean-project"
        temp_root.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=temp_root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        env = os.environ.copy()
        env.update(
            {
                "LOBSTER_BUFFET_ADAPTER_CONFIG": "fixtures/adapters/local-project-command-adapter-config.v0.1.0.json",
                "LOBSTER_BUFFET_LOCAL_PROJECT_ROOT": str(temp_root),
                "LOBSTER_BUFFET_LOCAL_PROJECT_KIND": "software",
                "LOBSTER_BUFFET_LOCAL_PROJECT_PRIVACY": "public",
            }
        )

        result = run_json(["python3", "-m", "lobster_buffet.cli", "project", "inspect"], env)
    errors: list[str] = []

    repo = result.get("repo", {})
    if not repo.get("is_git_repo"):
        errors.append("local project adapter did not report the repository as a git repo")
    if repo.get("dirty") is not False:
        errors.append("local project adapter reported a clean repository as dirty")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print("Validated local project adapter clean git status.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

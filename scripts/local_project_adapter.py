#!/usr/bin/env python3
"""Local command adapter for redacted project.inspect-style capabilities."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ADAPTER_API = "lobster-buffet.local-adapter.v0"
INVOCATION_SCHEMA = "lobster-buffet.local-adapter-invocation.v0.1.0"
FIXTURE_SCHEMA = "lobster-buffet.local-adapter-fixture.v0.1.0"
PROJECT_ROOT_ENV = "LOBSTER_BUFFET_LOCAL_PROJECT_ROOT"
PROJECT_KIND_ENV = "LOBSTER_BUFFET_LOCAL_PROJECT_KIND"
PROJECT_PRIVACY_ENV = "LOBSTER_BUFFET_LOCAL_PROJECT_PRIVACY"
DEFAULT_PROJECT_PRIVACY = "internal"


def envelope(capability: str, result: dict[str, Any], disclosure_policy: str) -> dict[str, Any]:
    return {
        "name": capability,
        "envelope": {
            "ok": True,
            "capability": capability,
            "result": result,
            "warnings": [],
            "private_data": {
                "contains_private_values": False,
                "private_refs_only": True,
                "disclosure_policy": disclosure_policy,
            },
        },
    }


def error(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def read_invocation() -> dict[str, Any]:
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise ValueError("adapter invocation request was not valid JSON") from exc
    if request.get("schema") != INVOCATION_SCHEMA:
        raise ValueError("unsupported adapter invocation schema")
    if request.get("adapter_api") != ADAPTER_API:
        raise ValueError("unsupported adapter API")
    return request


def project_root() -> Path:
    configured = os.environ.get(PROJECT_ROOT_ENV)
    if not configured:
        raise ValueError(f"{PROJECT_ROOT_ENV} is required for the local project adapter")
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"{PROJECT_ROOT_ENV} does not point to a directory")
    return root


def git_output(root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def git_status(root: Path) -> dict[str, Any]:
    try:
        inside = git_output(root, ["rev-parse", "--is-inside-work-tree"]) == "true"
        branch = git_output(root, ["branch", "--show-current"]) or "detached"
        status_lines = git_output(root, ["status", "--porcelain=v1", "--branch"]).splitlines()
    except subprocess.CalledProcessError:
        return {
            "repo": {
                "is_git_repo": False,
                "branch": "unknown",
                "dirty": False,
                "ahead": 0,
                "behind": 0,
            },
            "worktree": {
                "changed_count": 0,
                "untracked_count": 0,
            },
            "remote": {
                "has_remote": False,
                "remote_ref": "none",
            },
        }

    ahead = 0
    behind = 0
    changed = 0
    untracked = 0
    for line in status_lines:
        if line.startswith("## ") and "[" in line:
            marker = line.split("[", 1)[1].split("]", 1)[0]
            for part in marker.split(", "):
                if part.startswith("ahead "):
                    ahead = int(part.removeprefix("ahead "))
                if part.startswith("behind "):
                    behind = int(part.removeprefix("behind "))
            continue
        if line.startswith("??"):
            untracked += 1
        elif line:
            changed += 1

    remotes = git_output(root, ["remote"]).splitlines()
    return {
        "repo": {
            "is_git_repo": inside,
            "branch": branch,
            "dirty": bool(changed or untracked),
            "ahead": ahead,
            "behind": behind,
        },
        "worktree": {
            "changed_count": changed,
            "untracked_count": untracked,
        },
        "remote": {
            "has_remote": bool(remotes),
            "remote_ref": remotes[0] if remotes else "none",
        },
    }


def checkbox_counts(backlog: str) -> dict[str, int]:
    return {
        "open_next": backlog.count("- [ ]"),
        "open_later": 0,
        "done": backlog.count("- [x]"),
    }


def section_count(backlog: str, section: str, marker: str) -> int:
    current = None
    total = 0
    for line in backlog.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            continue
        if current == section and marker in line:
            total += 1
    return total


def lifecycle_state(root: Path) -> str:
    state_file = root / "LIFECYCLE_STATE.md"
    if not state_file.exists():
        return "unknown"
    for line in state_file.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("state:"):
            return line.split(":", 1)[1].strip() or "unknown"
    return "unknown"


def first_content_line(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        stripped = stripped.strip(" #")
        if stripped:
            return stripped
    return fallback


def metadata(root: Path) -> dict[str, Any]:
    backlog_text = (root / "BACKLOG.md").read_text(encoding="utf-8") if (root / "BACKLOG.md").exists() else ""
    counts = checkbox_counts(backlog_text)
    counts["open_next"] = section_count(backlog_text, "Next", "- [ ]")
    counts["open_later"] = section_count(backlog_text, "Later", "- [ ]")
    return {
        "project": {
            "name": root.name,
            "kind": os.environ.get(PROJECT_KIND_ENV, "software"),
            "lifecycle_state": lifecycle_state(root),
            "privacy": os.environ.get(PROJECT_PRIVACY_ENV, DEFAULT_PROJECT_PRIVACY),
        },
        "backlog": counts,
        "intent": {
            "goal": first_content_line(root / "docs" / "GOAL.md", "No goal document found."),
            "current_priority": first_content_line(root / "BACKLOG.md", "No backlog found."),
            "non_goals": [],
        },
        "metadata_refs": [
            ref
            for ref in ("BACKLOG.md", "docs/GOAL.md", "docs/PRODUCT_BRIEF.md", "LIFECYCLE_STATE.md")
            if (root / ref).exists()
        ],
    }


def capabilities(root: Path, requested: list[str]) -> list[dict[str, Any]]:
    project_name = root.name
    available = {
        "project.resolve": envelope(
            "project.resolve",
            {
                "project_ref": f"local-project:{project_name}",
                "project_name": project_name,
                "kind": os.environ.get(PROJECT_KIND_ENV, "software"),
                "lifecycle_state": lifecycle_state(root),
                "privacy": os.environ.get(PROJECT_PRIVACY_ENV, DEFAULT_PROJECT_PRIVACY),
            },
            "opaque_ref",
        ),
        "filesystem.read_project_metadata": envelope(
            "filesystem.read_project_metadata",
            metadata(root),
            "redacted_summary",
        ),
        "git.inspect_status": envelope(
            "git.inspect_status",
            git_status(root),
            "redacted_summary",
        ),
    }
    names = requested or list(available)
    return [available[name] for name in names if name in available]


def main() -> int:
    try:
        request = read_invocation()
        root = project_root()
    except ValueError as exc:
        return error(str(exc))

    requested = [item for item in request.get("requested_capabilities", []) if isinstance(item, str)]
    result = {
        "schema": FIXTURE_SCHEMA,
        "fixture_id": "local-project-adapter-runtime",
        "adapter_api": ADAPTER_API,
        "capabilities": capabilities(root, requested),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

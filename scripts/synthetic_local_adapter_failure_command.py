#!/usr/bin/env python3
"""Synthetic local adapter command for command-backend failure-path tests."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_fixture(value: str) -> dict[str, Any]:
    fixture_path = Path(value)
    if not fixture_path.is_absolute():
        fixture_path = ROOT / fixture_path
    return load_json(fixture_path)


def filter_requested(fixture: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    requested = set(request.get("requested_capabilities", []))
    if not requested:
        return fixture
    return {
        **fixture,
        "capabilities": [item for item in fixture["capabilities"] if item["name"] in requested],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "usage: synthetic_local_adapter_failure_command.py <fixture> "
            "<invalid-json|nonzero-exit|timeout|missing-capability> [capability]",
            file=sys.stderr,
        )
        return 2

    fixture_path, mode, *rest = argv[1:]

    if mode == "invalid-json":
        print("{not valid json")
        return 0

    if mode == "nonzero-exit":
        print("synthetic adapter command failed before returning a fixture", file=sys.stderr)
        return 3

    if mode == "timeout":
        time.sleep(2)
        print(json.dumps(load_fixture(fixture_path), indent=2, sort_keys=True))
        return 0

    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("adapter invocation request was not valid JSON", file=sys.stderr)
        return 1

    if request.get("schema") != "lobster-buffet.local-adapter-invocation.v0.1.0":
        print("unsupported adapter invocation schema", file=sys.stderr)
        return 1
    if request.get("adapter_api") != "lobster-buffet.local-adapter.v0":
        print("unsupported adapter API", file=sys.stderr)
        return 1

    if mode == "missing-capability":
        capability = rest[0] if rest else "git.write_branch"
        fixture = filter_requested(load_fixture(fixture_path), request)
        fixture = {
            **fixture,
            "capabilities": [item for item in fixture["capabilities"] if item["name"] != capability],
        }
        print(json.dumps(fixture, indent=2, sort_keys=True))
        return 0

    print(f"unsupported synthetic failure mode: {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

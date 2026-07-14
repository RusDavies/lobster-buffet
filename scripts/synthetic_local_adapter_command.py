#!/usr/bin/env python3
"""Synthetic local adapter command used to test command-backed invocation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: synthetic_local_adapter_command.py <fixture>", file=sys.stderr)
        return 2

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

    fixture_path = Path(argv[1])
    if not fixture_path.is_absolute():
        fixture_path = ROOT / fixture_path
    fixture = load_json(fixture_path)

    requested = set(request.get("requested_capabilities", []))
    if requested:
        fixture = {
            **fixture,
            "capabilities": [item for item in fixture["capabilities"] if item["name"] in requested],
        }

    print(json.dumps(fixture, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

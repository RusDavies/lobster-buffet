from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import core


def emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lobster-buffet")
    subparsers = parser.add_subparsers(dest="group", required=True)

    command = subparsers.add_parser("command")
    command_subparsers = command.add_subparsers(dest="action", required=True)

    command_list = command_subparsers.add_parser("list")
    command_list.add_argument("--detail", choices=["summary", "full"], default="summary")
    command_list.add_argument("--include-deprecated", action="store_true")

    command_describe = command_subparsers.add_parser("describe")
    command_describe.add_argument("--name", required=True)

    project = subparsers.add_parser("project")
    project_subparsers = project.add_subparsers(dest="action", required=True)

    project_inspect = project_subparsers.add_parser("inspect")
    project_inspect.add_argument(
        "--adapter-fixture",
        default="fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
    )

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.group == "command" and args.action == "list":
            emit(core.command_list(include_deprecated=args.include_deprecated))
            return 0

        if args.group == "command" and args.action == "describe":
            emit(core.command_describe(args.name))
            return 0

        if args.group == "project" and args.action == "inspect":
            emit(core.project_inspect(Path(args.adapter_fixture)))
            return 0

    except core.OperationError as error:
        emit(error.to_result())
        return 1

    parser.error("unsupported command")
    return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()

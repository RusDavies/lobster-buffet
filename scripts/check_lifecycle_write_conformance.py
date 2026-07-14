#!/usr/bin/env python3
"""Validate lifecycle write adapter fixtures against the apply-mode contract."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_initial_operation_schemas import load_json, validate  # noqa: E402


REQUIRED_CAPABILITIES = {
    "project.resolve",
    "git.inspect_status",
    "approval.request",
    "filesystem.write_project_files",
    "git.write_branch",
}

DEFAULT_CASES = [
    ("fixtures/adapters/synthetic-lifecycle-apply-approved.v0.1.0.json", "applied", True),
    ("fixtures/adapters/synthetic-lifecycle-apply-approval-missing.v0.1.0.json", "requires_approval", False),
    ("fixtures/adapters/synthetic-lifecycle-apply-dirty-git.v0.1.0.json", "blocked", False),
    ("fixtures/adapters/synthetic-lifecycle-apply-stale-approval.v0.1.0.json", "blocked", False),
]

DEFAULT_CONFIG_CASES = [
    ("fixtures/adapters/synthetic-command-lifecycle-apply-config.v0.1.0.json", "applied", True),
]


def run_json(command: list[str]) -> Any:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def capability_map(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item["envelope"] for item in fixture["capabilities"]}


def embedded_receipt(capabilities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "lobster-buffet.lifecycle-apply-receipt.v0.1.0",
        "operation_family": "project_lifecycle",
        "operation": "project.archive",
        "status": "applied",
        "mutates": True,
        "receipts": [
            capabilities["filesystem.write_project_files"]["result"]["receipt"],
            capabilities["git.write_branch"]["result"]["receipt"],
        ],
        "privacy": {
            "private_refs_only": True,
            "disclosure_policy": "local_adapter_controlled",
        },
    }


def validate_fixture(path: Path, expect_status: str, expect_mutates: bool) -> list[str]:
    errors: list[str] = []
    fixture = load_json(path)
    fixture_errors = validate(load_json(ROOT / "schemas/local-adapter-fixture.v0.1.0.json"), fixture)
    errors.extend(f"{path}: fixture {error}" for error in fixture_errors)

    capabilities = capability_map(fixture)
    missing = sorted(REQUIRED_CAPABILITIES - set(capabilities))
    if missing:
        errors.append(f"{path}: missing lifecycle write capabilities: {', '.join(missing)}")

    if expect_status == "applied" and not missing:
        receipt = embedded_receipt(capabilities)
        receipt_errors = validate(load_json(ROOT / "schemas/lifecycle-apply-receipt.v0.1.0.json"), receipt)
        errors.extend(f"{path}: embedded receipt {error}" for error in receipt_errors)

    result = run_json(
        [
            "python3",
            "-m",
            "lobster_buffet.cli",
            "project",
            "archive",
            "--project-name",
            "synthetic-project",
            "--mode",
            "apply",
            "--adapter-fixture",
            str(path.relative_to(ROOT)),
        ]
    )
    output_errors = validate(load_json(ROOT / "schemas/operations/project.lifecycle.output.v0.1.0.json"), result)
    errors.extend(f"{path}: lifecycle output {error}" for error in output_errors)

    if result.get("status") != expect_status:
        errors.append(f"{path}: expected status {expect_status!r}, got {result.get('status')!r}")
    if result.get("mutates") is not expect_mutates:
        errors.append(f"{path}: expected mutates {expect_mutates!r}, got {result.get('mutates')!r}")

    serialized = json.dumps({"fixture": fixture, "result": result}, sort_keys=True)
    for fragment in ("channel:", "0000000000000000000", "/home/", "github.com/RusDavies"):
        if fragment in serialized:
            errors.append(f"{path}: contains forbidden private/local fragment {fragment!r}")

    return errors


def validate_config(path: Path, expect_status: str, expect_mutates: bool) -> list[str]:
    errors: list[str] = []
    config = load_json(path)
    config_errors = validate(load_json(ROOT / "schemas/local-adapter-config.v0.1.0.json"), config)
    errors.extend(f"{path}: config {error}" for error in config_errors)

    result = run_json(
        [
            "python3",
            "-m",
            "lobster_buffet.cli",
            "project",
            "archive",
            "--project-name",
            "synthetic-project",
            "--mode",
            "apply",
            "--adapter-config",
            str(path.relative_to(ROOT)),
        ]
    )
    output_errors = validate(load_json(ROOT / "schemas/operations/project.lifecycle.output.v0.1.0.json"), result)
    errors.extend(f"{path}: lifecycle output {error}" for error in output_errors)

    if result.get("status") != expect_status:
        errors.append(f"{path}: expected status {expect_status!r}, got {result.get('status')!r}")
    if result.get("mutates") is not expect_mutates:
        errors.append(f"{path}: expected mutates {expect_mutates!r}, got {result.get('mutates')!r}")

    serialized = json.dumps({"config": config, "result": result}, sort_keys=True)
    for fragment in ("channel:", "0000000000000000000", "/home/", "github.com/RusDavies"):
        if fragment in serialized:
            errors.append(f"{path}: contains forbidden private/local fragment {fragment!r}")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter-fixture", default=None, help="Single adapter fixture to validate.")
    parser.add_argument("--adapter-config", default=None, help="Single adapter config to validate.")
    parser.add_argument("--expect-status", choices=["applied", "requires_approval", "blocked"], default="applied")
    parser.add_argument("--expect-mutates", choices=["true", "false"], default="true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.adapter_fixture and args.adapter_config:
        print("--adapter-fixture and --adapter-config are mutually exclusive", file=sys.stderr)
        return 2

    if args.adapter_fixture:
        cases = [(args.adapter_fixture, args.expect_status, args.expect_mutates == "true")]
        config_cases: list[tuple[str, str, bool]] = []
    elif args.adapter_config:
        cases = []
        config_cases = [(args.adapter_config, args.expect_status, args.expect_mutates == "true")]
    else:
        cases = DEFAULT_CASES
        config_cases = DEFAULT_CONFIG_CASES

    errors: list[str] = []
    for fixture, expect_status, expect_mutates in cases:
        errors.extend(validate_fixture(ROOT / fixture, expect_status, expect_mutates))
    for config, expect_status, expect_mutates in config_cases:
        errors.extend(validate_config(ROOT / config, expect_status, expect_mutates))

    if errors:
        print("\n".join(errors))
        return 1

    print(f"Validated {len(cases) + len(config_cases)} lifecycle write conformance case(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

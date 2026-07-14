#!/usr/bin/env python3
"""Validate command-backed adapter failure paths."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_initial_operation_schemas import load_json, validate  # noqa: E402


ERROR_CASES = [
    ("fixtures/adapters/synthetic-command-invalid-json-config.v0.1.0.json", "adapter.command_invalid_json"),
    ("fixtures/adapters/synthetic-command-nonzero-exit-config.v0.1.0.json", "adapter.command_failed"),
    ("fixtures/adapters/synthetic-command-timeout-config.v0.1.0.json", "adapter.command_timeout"),
]
BLOCKED_CASES = [
    (
        "fixtures/adapters/synthetic-command-missing-capability-config.v0.1.0.json",
        "blocked",
        False,
        "Adapter fixture is missing apply capability git.write_branch.",
    ),
]


def run_lifecycle(config: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
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
            config,
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_stdout(path: str, completed: subprocess.CompletedProcess[str]) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        return json.loads(completed.stdout), []
    except json.JSONDecodeError as error:
        return None, [f"{path}: stdout was not JSON: {error}"]


def validate_error_case(path: str, expect_code: str) -> list[str]:
    errors: list[str] = []
    completed = run_lifecycle(path)
    output, parse_errors = parse_stdout(path, completed)
    errors.extend(parse_errors)
    if output is None:
        return errors

    if completed.returncode != 1:
        errors.append(f"{path}: expected exit 1, got {completed.returncode}")
    error = output.get("error", {})
    if error.get("code") != expect_code:
        errors.append(f"{path}: expected error code {expect_code!r}, got {error.get('code')!r}")
    if error.get("retryable") is not False:
        errors.append(f"{path}: expected retryable=false")
    if completed.stderr.strip():
        errors.append(f"{path}: CLI leaked stderr instead of returning a JSON error envelope")
    return errors


def validate_blocked_case(path: str, expect_status: str, expect_mutates: bool, expect_warning: str) -> list[str]:
    errors: list[str] = []
    completed = run_lifecycle(path)
    output, parse_errors = parse_stdout(path, completed)
    errors.extend(parse_errors)
    if output is None:
        return errors

    if completed.returncode != 0:
        errors.append(f"{path}: expected exit 0 for blocked lifecycle result, got {completed.returncode}")
    output_errors = validate(load_json(ROOT / "schemas/operations/project.lifecycle.output.v0.1.0.json"), output)
    errors.extend(f"{path}: lifecycle output {error}" for error in output_errors)
    if output.get("status") != expect_status:
        errors.append(f"{path}: expected status {expect_status!r}, got {output.get('status')!r}")
    if output.get("mutates") is not expect_mutates:
        errors.append(f"{path}: expected mutates {expect_mutates!r}, got {output.get('mutates')!r}")
    if expect_warning not in output.get("warnings", []):
        errors.append(f"{path}: missing expected warning {expect_warning!r}")
    return errors


def main() -> int:
    errors: list[str] = []
    config_schema = load_json(ROOT / "schemas/local-adapter-config.v0.1.0.json")
    for path, expect_code in ERROR_CASES:
        config_errors = validate(config_schema, load_json(ROOT / path))
        errors.extend(f"{path}: config {error}" for error in config_errors)
        errors.extend(validate_error_case(path, expect_code))
    for path, expect_status, expect_mutates, expect_warning in BLOCKED_CASES:
        config_errors = validate(config_schema, load_json(ROOT / path))
        errors.extend(f"{path}: config {error}" for error in config_errors)
        errors.extend(validate_blocked_case(path, expect_status, expect_mutates, expect_warning))

    if errors:
        print("\n".join(errors))
        return 1

    print(f"Validated {len(ERROR_CASES) + len(BLOCKED_CASES)} command adapter failure conformance case(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

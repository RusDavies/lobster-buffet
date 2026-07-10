#!/usr/bin/env python3
"""Run the first CLI-core operations and validate their JSON outputs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_initial_operation_schemas import load_json, validate  # noqa: E402


COMMANDS = [
    (
        ["python3", "-m", "lobster_buffet.cli", "command", "list"],
        ROOT / "schemas/operations/command.list.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "command", "describe", "--name", "project.inspect"],
        ROOT / "schemas/operations/command.describe.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "project", "inspect"],
        ROOT / "schemas/operations/project.inspect.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "operation", "plan", "--name", "project.inspect"],
        ROOT / "schemas/operation-plan.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "git", "workflow-guard"],
        ROOT / "schemas/operations/git.workflow.guard.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "incident", "list"],
        ROOT / "schemas/operations/incident.list.output.v0.1.0.json",
    ),
    (
        [
            "python3",
            "-m",
            "lobster_buffet.cli",
            "alignment",
            "scan",
            "--current-plan-summary",
            "Implement an intent-alignment scanner.",
        ],
        ROOT / "schemas/operations/alignment.scan.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "review", "list"],
        ROOT / "schemas/operations/review.list.output.v0.1.0.json",
    ),
    (
        [
            "python3",
            "-m",
            "lobster_buffet.cli",
            "review",
            "update",
            "--review-id",
            "review-001",
            "--kind",
            "approval",
            "--summary",
            "Plan approval after review evidence is accepted.",
            "--apply-gate",
            "approved",
        ],
        ROOT / "schemas/operations/review.update.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "heartbeat", "packet"],
        ROOT / "schemas/operations/heartbeat.packet.output.v0.1.0.json",
    ),
    (
        ["python3", "-m", "lobster_buffet.cli", "heartbeat", "check"],
        ROOT / "schemas/operations/heartbeat.check.output.v0.1.0.json",
    ),
]

for action in ("bootstrap", "adopt", "repair", "migrate", "archive"):
    COMMANDS.append(
        (
            [
                "python3",
                "-m",
                "lobster_buffet.cli",
                "project",
                action,
                "--project-name",
                "synthetic-project",
            ],
            ROOT / "schemas/operations/project.lifecycle.output.v0.1.0.json",
        )
    )


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


def main() -> int:
    errors: list[str] = []
    for command, schema_path in COMMANDS:
        output = run_json(command)
        schema = load_json(schema_path)
        validation_errors = validate(schema, output)
        if validation_errors:
            errors.append(f"{' '.join(command)} failed {schema_path.relative_to(ROOT)}")
            errors.extend(f"  {error}" for error in validation_errors)

    project_output = run_json(["python3", "-m", "lobster_buffet.cli", "project", "inspect"])
    incident_output = run_json(["python3", "-m", "lobster_buffet.cli", "incident", "list"])
    alignment_output = run_json(["python3", "-m", "lobster_buffet.cli", "alignment", "scan"])
    review_output = run_json(["python3", "-m", "lobster_buffet.cli", "review", "list"])
    review_update_output = run_json(
        [
            "python3",
            "-m",
            "lobster_buffet.cli",
            "review",
            "update",
            "--review-id",
            "review-001",
            "--kind",
            "approval",
            "--summary",
            "Plan approval after review evidence is accepted.",
            "--apply-gate",
            "approved",
        ]
    )
    heartbeat_output = run_json(["python3", "-m", "lobster_buffet.cli", "heartbeat", "packet"])
    heartbeat_check_output = run_json(["python3", "-m", "lobster_buffet.cli", "heartbeat", "check"])
    git_guard_output = run_json(["python3", "-m", "lobster_buffet.cli", "git", "workflow-guard"])
    plan_output = run_json(["python3", "-m", "lobster_buffet.cli", "operation", "plan", "--name", "project.inspect"])
    output_text = json.dumps(
        {
            "alignment": alignment_output,
            "heartbeat": heartbeat_output,
            "heartbeat_check": heartbeat_check_output,
            "git_guard": git_guard_output,
            "incident": incident_output,
            "plan": plan_output,
            "project": project_output,
            "review": review_output,
            "review_update": review_update_output,
        },
        sort_keys=True,
    )
    for fragment in ("channel:", "0000000000000000000", "/home/", "github.com/RusDavies"):
        if fragment in output_text:
            errors.append(f"project.inspect output contains forbidden private/local fragment {fragment!r}")

    if not any(incident["status"] == "stale" and incident["resurface"] for incident in incident_output["incidents"]):
        errors.append("incident.list did not include a stale incident marked for resurfacing")

    if alignment_output["verdict"] != "aligned":
        errors.append("alignment.scan did not return an aligned verdict for synthetic provider-boundary work")

    if not any(review["status"] == "active" and review["apply_gate"] == "pending" for review in review_output["reviews"]):
        errors.append("review.list did not include an active review with a pending apply gate")

    if review_update_output["status"] != "requires_approval" or review_update_output["mutates"] is not False:
        errors.append("review.update did not return a non-mutating approval preview")

    if heartbeat_output["overall_status"] != "blocked":
        errors.append("heartbeat.packet did not return blocked status for the synthetic blocked review")

    if heartbeat_check_output["status"] != "not_due" or heartbeat_check_output["due"] is not False:
        errors.append("heartbeat.check did not return not_due for synthetic heartbeat state")

    if git_guard_output["decision"] != "allowed":
        errors.append("git.workflow.guard did not return allowed for synthetic clean git state")

    if errors:
        print("\n".join(errors))
        return 1

    print(f"Validated {len(COMMANDS)} CLI-core operation(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

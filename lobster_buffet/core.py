from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_FIXTURE = "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json"
ADAPTER_CONFIG_ENV = "LOBSTER_BUFFET_ADAPTER_CONFIG"
LIFECYCLE_ACTIONS = ("bootstrap", "adopt", "repair", "migrate", "archive")
GIT_WORKFLOW_ACTIONS = ("branch", "commit", "merge", "push", "release", "lifecycle_apply")
REVIEW_UPDATE_KINDS = ("comment", "decision", "approval", "blocker", "note")
REVIEW_APPLY_GATES = ("none", "pending", "approved", "blocked")
LIFECYCLE_APPLY_CAPABILITIES = (
    "project.resolve",
    "filesystem.write_project_files",
    "git.inspect_status",
    "git.write_branch",
    "approval.request",
)


class OperationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_result(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": False,
                "details": {},
            }
        }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(value: str | Path, base: Path = ROOT) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base / path


def operation_catalog() -> dict[str, Any]:
    return load_json(ROOT / "manifests/operation-catalog.v0.1.0.json")


def provider_manifest() -> dict[str, Any]:
    return load_json(ROOT / "manifests/provider-operations.v0.1.0.json")


def catalog_operation(name: str) -> dict[str, Any]:
    for operation in operation_catalog()["operations"]:
        if operation["name"] == name:
            return operation
    raise OperationError("catalog.command_not_found", f"Unknown operation: {name}")


def manifest_operation(name: str) -> dict[str, Any]:
    for operation in provider_manifest()["operations"]:
        if operation["name"] == name:
            return operation
    raise OperationError("catalog.command_not_found", f"Operation has no schema-backed manifest entry: {name}")


def affected_surfaces_for(operation: dict[str, Any]) -> list[dict[str, str]]:
    kinds: list[str] = []
    for capability in operation["adapter_capabilities"]:
        if capability.startswith("project.") or capability.startswith("filesystem."):
            kinds.append("project")
        elif capability.startswith("git."):
            kinds.append("repository")
        elif capability.startswith("incident."):
            kinds.append("incident_store")
        elif capability.startswith("review."):
            kinds.append("review_store")
        elif capability.startswith("heartbeat."):
            kinds.append("heartbeat_state")
        elif capability.startswith("channel."):
            kinds.append("channel")
        elif capability.startswith("remote."):
            kinds.append("remote")
        elif capability.startswith("visible_message."):
            kinds.append("visible_message")
        elif capability.startswith("approval."):
            kinds.append("approval")
        elif capability.startswith("secret."):
            kinds.append("secret")

    if "message.visible_send" in operation["side_effects"]:
        kinds.append("visible_message")
    if "secret.read" in operation["side_effects"]:
        kinds.append("secret")
    if any(effect.startswith("network.") for effect in operation["side_effects"]):
        kinds.append("network")

    deduped = list(dict.fromkeys(kinds))
    if not deduped:
        deduped = ["operation_catalog"]
    return [{"kind": kind, "ref_policy": "category_only"} for kind in deduped]


def approval_reason(approval: dict[str, Any], read_only: bool) -> str:
    if approval["required"]:
        return "Operation declares approval classes before execution."
    if read_only:
        return "Read-only operation; no approval required before execution."
    return "No approval required by current manifest."


def operation_plan(name: str, actor_ref: str = "local-actor-ref", surface: str = "unknown") -> dict[str, Any]:
    manifest_entry = manifest_operation(name)
    catalog_entry = catalog_operation(name)
    return {
        "schema": "lobster-buffet.operation-plan.v0.1.0",
        "plan_id": f"plan:{manifest_entry['name']}:v{manifest_entry['version']}",
        "operation": {
            "namespace": "lobster-buffet",
            "name": manifest_entry["name"],
            "version": manifest_entry["version"],
            "stability": manifest_entry["stability"],
        },
        "requested_by": {
            "actor_ref": actor_ref,
            "surface": surface,
        },
        "input_summary": {
            "redaction": "private_refs",
            "fields": {
                "operation": manifest_entry["name"],
            },
        },
        "side_effects": manifest_entry["side_effects"],
        "approval": {
            "required": manifest_entry["approval"]["required"],
            "classes": manifest_entry["approval"]["classes"],
            "reason": approval_reason(manifest_entry["approval"], manifest_entry["read_only"]),
        },
        "adapter_capabilities": manifest_entry["adapter_capabilities"],
        "affected_surfaces": affected_surfaces_for(manifest_entry),
        "verification": [
            {
                "kind": "schema",
                "description": f"Validate result against {manifest_entry['output_schema_ref']}.",
            }
        ],
        "privacy": {
            "contains_private_values": False,
            "private_refs_only": True,
            "disclosure_policy": "local_adapter_controlled",
        },
        "summary": catalog_entry["summary"],
    }


def command_list(include_deprecated: bool = False) -> dict[str, Any]:
    operations = []
    for operation in operation_catalog()["operations"]:
        if operation["stability"] == "deprecated" and not include_deprecated:
            continue
        operations.append(
            {
                "name": operation["name"],
                "version": operation["version"],
                "family": operation["family"],
                "stability": operation["stability"],
                "implementation_state": operation["implementation_state"],
                "read_only": operation["read_only"],
                "side_effects": operation["side_effects"],
                "summary": operation["summary"],
            }
        )
    return {"operations": operations}


def command_describe(name: str) -> dict[str, Any]:
    manifest_entry = manifest_operation(name)
    catalog_entry = catalog_operation(name)
    return {
        "operation": {
            "name": manifest_entry["name"],
            "version": manifest_entry["version"],
            "stability": manifest_entry["stability"],
        },
        "summary": catalog_entry["summary"],
        "inputs": {
            "schema_ref": manifest_entry["input_schema_ref"],
        },
        "outputs": {
            "schema_ref": manifest_entry["output_schema_ref"],
        },
        "side_effects": manifest_entry["side_effects"],
        "approval": manifest_entry["approval"],
        "adapter_capabilities": manifest_entry["adapter_capabilities"],
        "errors": manifest_entry["errors"],
    }


def load_adapter_fixture(path: Path) -> dict[str, Any]:
    fixture = load_json(path)
    return {item["name"]: item["envelope"] for item in fixture["capabilities"]}


def default_adapter_config_path() -> Path | None:
    configured = os.environ.get(ADAPTER_CONFIG_ENV)
    if not configured:
        return None
    return Path(configured)


def load_adapter_config(path: Path) -> dict[str, Any]:
    config = load_json(path)
    if config.get("schema") != "lobster-buffet.local-adapter-config.v0.1.0":
        raise OperationError("adapter.config_invalid", f"Unsupported adapter config schema: {path}")
    if config.get("adapter_api") != "lobster-buffet.local-adapter.v0":
        raise OperationError("adapter.config_invalid", f"Unsupported adapter API in config: {path}")
    backend = config.get("backend", {})
    kind = backend.get("kind")
    if kind == "fixture":
        fixture_path = backend.get("fixture_path")
        if not fixture_path:
            raise OperationError("adapter.config_invalid", "Fixture adapter config is missing backend.fixture_path.")
        return {
            "backend_kind": "fixture",
            "fixture_path": resolve_path(fixture_path, path.parent),
        }
    if kind == "command":
        command = backend.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(item, str) and item for item in command):
            raise OperationError("adapter.config_invalid", "Command adapter config requires a non-empty backend.command list.")
        return {
            "backend_kind": "command",
            "command": command,
            "timeout_seconds": int(backend.get("timeout_seconds", 10)),
        }
    raise OperationError("adapter.config_invalid", f"Unsupported adapter backend kind: {kind}")


def invoke_adapter_command(
    command: list[str],
    timeout_seconds: int,
    operation_name: str | None = None,
    requested_capabilities: list[str] | None = None,
) -> dict[str, Any]:
    request = {
        "schema": "lobster-buffet.local-adapter-invocation.v0.1.0",
        "adapter_api": "lobster-buffet.local-adapter.v0",
        "operation": operation_name or "unknown",
        "requested_capabilities": requested_capabilities or [],
    }
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            input=json.dumps(request),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=True,
        )
    except subprocess.TimeoutExpired as error:
        raise OperationError("adapter.command_timeout", f"Adapter command timed out after {timeout_seconds}s") from error
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or "Adapter command failed."
        raise OperationError("adapter.command_failed", message) from error

    try:
        fixture = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise OperationError("adapter.command_invalid_json", "Adapter command did not return valid JSON.") from error

    return {item["name"]: item["envelope"] for item in fixture["capabilities"]}


def load_adapter(
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
    operation_name: str | None = None,
    requested_capabilities: list[str] | None = None,
) -> dict[str, Any]:
    if adapter_fixture_path is not None:
        return load_adapter_fixture(resolve_path(adapter_fixture_path))

    config_path = adapter_config_path or default_adapter_config_path()
    if config_path is None:
        return load_adapter_fixture(resolve_path(DEFAULT_ADAPTER_FIXTURE))

    config = load_adapter_config(resolve_path(config_path))
    if config["backend_kind"] == "fixture":
        return load_adapter_fixture(config["fixture_path"])
    return invoke_adapter_command(
        config["command"],
        config["timeout_seconds"],
        operation_name=operation_name,
        requested_capabilities=requested_capabilities,
    )


def require_fixture_capability(fixture: dict[str, Any], capability: str) -> dict[str, Any]:
    envelope = fixture.get(capability)
    if envelope is None:
        raise OperationError("adapter.capability_missing", f"Adapter fixture is missing {capability}")
    if not envelope["ok"]:
        raise OperationError("adapter.capability_failed", f"Adapter fixture capability failed: {capability}")
    return envelope


def project_inspect(
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="project.inspect",
        requested_capabilities=["project.resolve", "filesystem.read_project_metadata", "git.inspect_status"],
    )
    project = require_fixture_capability(fixture, "project.resolve")["result"]
    metadata = require_fixture_capability(fixture, "filesystem.read_project_metadata")["result"]
    git_status = require_fixture_capability(fixture, "git.inspect_status")["result"]

    return {
        "project": {
            "name": metadata["project"]["name"],
            "kind": metadata["project"]["kind"],
            "lifecycle_state": metadata["project"]["lifecycle_state"],
            "privacy": metadata["project"]["privacy"],
        },
        "repo": git_status["repo"],
        "backlog": metadata["backlog"],
        "capabilities": {
            "can_read_files": True,
            "can_inspect_git": True,
            "can_mutate": False,
        },
        "warnings": [] if project.get("project_ref") else ["project reference missing"],
    }


def git_workflow_guard(
    requested_action: str = "lifecycle_apply",
    detail: str = "summary",
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if requested_action not in GIT_WORKFLOW_ACTIONS:
        raise OperationError("input.invalid", f"Unsupported git workflow action: {requested_action}")
    if detail not in {"summary", "full"}:
        raise OperationError("input.invalid", f"Unsupported git workflow guard detail level: {detail}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="git.workflow.guard",
        requested_capabilities=["git.inspect_status"],
    )
    git_status = require_fixture_capability(fixture, "git.inspect_status")["result"]
    repo = git_status.get("repo", {})
    worktree = git_status.get("worktree", {})
    sync = git_status.get("sync", {})

    checks: list[dict[str, str]] = []
    if not repo.get("is_git_repo", True):
        checks.append(
            {
                "kind": "repo",
                "status": "blocker",
                "summary": "Project reference is not a git repository.",
            }
        )
    else:
        checks.append(
            {
                "kind": "repo",
                "status": "pass",
                "summary": f"Git repository is readable on branch {repo.get('branch', 'unknown')}.",
            }
        )

    changed_count = int(worktree.get("changed_count", 0))
    untracked_count = int(worktree.get("untracked_count", 0))
    if repo.get("dirty") or changed_count or untracked_count:
        checks.append(
            {
                "kind": "worktree",
                "status": "blocker",
                "summary": f"Worktree has {changed_count} changed and {untracked_count} untracked file(s).",
            }
        )
    else:
        checks.append(
            {
                "kind": "worktree",
                "status": "pass",
                "summary": "Worktree is clean in adapter state.",
            }
        )

    ahead = int(sync.get("ahead", 0))
    behind = int(sync.get("behind", 0))
    if behind:
        checks.append(
            {
                "kind": "sync",
                "status": "blocker",
                "summary": f"Branch is behind upstream by {behind} commit(s).",
            }
        )
    elif ahead:
        checks.append(
            {
                "kind": "sync",
                "status": "warning",
                "summary": f"Branch is ahead of upstream by {ahead} commit(s).",
            }
        )
    elif detail == "full":
        checks.append(
            {
                "kind": "sync",
                "status": "pass",
                "summary": "Branch is in sync with upstream in adapter state.",
            }
        )

    blocked = any(check["status"] == "blocker" for check in checks)
    checks.append(
        {
            "kind": "action",
            "status": "blocker" if blocked else "pass",
            "summary": (
                f"{requested_action} is blocked until guard blockers are resolved."
                if blocked
                else f"{requested_action} can proceed to its next operation gate."
            ),
        }
    )

    return {
        "requested_action": requested_action,
        "decision": "blocked" if blocked else "allowed",
        "checks": checks,
        "next_actions": (
            ["Resolve blocker checks before mutation."]
            if blocked
            else ["Proceed to the next operation gate before mutation."]
        ),
    }


def incident_list(
    status: str = "active",
    detail: str = "summary",
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if status not in {"active", "stale", "closed", "all"}:
        raise OperationError("input.invalid", f"Unsupported incident status filter: {status}")
    if detail not in {"summary", "full"}:
        raise OperationError("input.invalid", f"Unsupported incident detail level: {detail}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="incident.list",
        requested_capabilities=["incident.read_state"],
    )
    incident_state = require_fixture_capability(fixture, "incident.read_state")["result"]
    incidents = incident_state.get("incidents", [])
    counts = {
        "active": sum(1 for incident in incidents if incident["status"] == "active"),
        "stale": sum(1 for incident in incidents if incident["status"] == "stale"),
        "closed": sum(1 for incident in incidents if incident["status"] == "closed"),
    }

    filtered = [
        incident
        for incident in incidents
        if status == "all" or incident["status"] == status or (status == "active" and incident.get("resurface") is True)
    ]
    filtered.sort(key=lambda incident: (not incident.get("resurface", False), incident["updated_at"], incident["id"]))

    return {
        "counts": counts,
        "incidents": [
            {
                "id": incident["id"],
                "status": incident["status"],
                "severity": incident["severity"],
                "title": incident["title"],
                "updated_at": incident["updated_at"],
                "resurface": bool(incident.get("resurface", incident["status"] == "stale")),
            }
            for incident in filtered
        ],
    }


def alignment_scan(
    source: str = "project",
    project: str | None = None,
    label: str | None = None,
    current_plan_summary: str | None = None,
    detail: str = "summary",
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if source not in {"project", "channel", "explicit"}:
        raise OperationError("input.invalid", f"Unsupported alignment context source: {source}")
    if detail not in {"summary", "full"}:
        raise OperationError("input.invalid", f"Unsupported alignment detail level: {detail}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="alignment.scan",
        requested_capabilities=["project.resolve", "filesystem.read_project_metadata", "git.inspect_status"],
    )
    project_ref = require_fixture_capability(fixture, "project.resolve")["result"]
    metadata = require_fixture_capability(fixture, "filesystem.read_project_metadata")["result"]
    git_status = require_fixture_capability(fixture, "git.inspect_status")["result"]

    findings: list[dict[str, str]] = []
    intent = metadata.get("intent", {})
    plan = (current_plan_summary or metadata.get("intent", {}).get("current_priority") or "").lower()
    non_goal_terms = {
        "portage packaging": "Plan appears to move Lobster Portage packaging work into the Buffet backlog.",
        "redshield implementation": "Plan appears to implement Redshield behavior inside the Buffet provider core.",
        "private workspace data": "Plan appears to include private workspace data in shared provider artifacts.",
        "hosted service": "Plan appears to introduce hosted-service scope before requirements are updated.",
    }

    if not project_ref.get("project_ref"):
        findings.append(
            {
                "kind": "unknown",
                "severity": "blocker",
                "summary": "Adapter did not return an opaque project reference.",
            }
        )

    if not intent:
        findings.append(
            {
                "kind": "intent",
                "severity": "warning",
                "summary": "Project metadata did not include an intent summary.",
            }
        )
    else:
        findings.append(
            {
                "kind": "intent",
                "severity": "info",
                "summary": intent.get("goal", "Project metadata includes an intent summary."),
            }
        )

    for term, summary in non_goal_terms.items():
        if term in plan:
            findings.append({"kind": "scope", "severity": "warning", "summary": summary})

    if git_status["repo"].get("dirty"):
        findings.append(
            {
                "kind": "artifact",
                "severity": "warning",
                "summary": "Repository has uncommitted changes; alignment evidence may be in flux.",
            }
        )

    if metadata.get("backlog", {}).get("open_next", 0) > 0:
        findings.append(
            {
                "kind": "backlog",
                "severity": "info",
                "summary": "Backlog has a current next item inside the provider boundary.",
            }
        )

    blocker_count = sum(1 for finding in findings if finding["severity"] == "blocker")
    warning_count = sum(1 for finding in findings if finding["severity"] == "warning")
    if blocker_count:
        verdict = "blocked"
    elif warning_count:
        verdict = "drifting"
    else:
        verdict = "aligned"

    next_actions = {
        "aligned": ["Proceed with the current provider-boundary work item."],
        "drifting": ["Pause and reconcile the plan against project intent before implementation."],
        "blocked": ["Resolve missing adapter evidence before continuing."],
    }[verdict]

    return {
        "verdict": verdict,
        "findings": findings if detail == "full" else findings[:3],
        "next_actions": next_actions,
    }


def review_list(
    status: str = "active",
    detail: str = "summary",
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if status not in {"active", "blocked", "closed", "all"}:
        raise OperationError("input.invalid", f"Unsupported review status filter: {status}")
    if detail not in {"summary", "full"}:
        raise OperationError("input.invalid", f"Unsupported review detail level: {detail}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="review.list",
        requested_capabilities=["review.read_state"],
    )
    review_state = require_fixture_capability(fixture, "review.read_state")["result"]
    reviews = review_state.get("reviews", [])
    counts = {
        "active": sum(1 for review in reviews if review["status"] == "active"),
        "blocked": sum(1 for review in reviews if review["status"] == "blocked"),
        "closed": sum(1 for review in reviews if review["status"] == "closed"),
    }

    filtered = [review for review in reviews if status == "all" or review["status"] == status]
    filtered.sort(key=lambda review: (review["status"] != "blocked", review["updated_at"], review["id"]))

    return {
        "counts": counts,
        "reviews": [
            {
                "id": review["id"],
                "status": review["status"],
                "title": review["title"],
                "updated_at": review["updated_at"],
                "pending_comments": review["pending_comments"],
                "apply_gate": review["apply_gate"],
            }
            for review in filtered
        ],
    }


def review_update_preview(
    review_id: str,
    kind: str,
    summary: str,
    mode: str = "plan",
    apply_gate: str | None = None,
    reason: str | None = None,
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if mode not in {"plan", "apply"}:
        raise OperationError("input.invalid", f"Unsupported review update mode: {mode}")
    if kind not in REVIEW_UPDATE_KINDS:
        raise OperationError("input.invalid", f"Unsupported review update kind: {kind}")
    if not review_id:
        raise OperationError("input.invalid", "Review id is required.")
    if not summary:
        raise OperationError("input.invalid", "Review update summary is required.")
    if apply_gate is not None and apply_gate not in REVIEW_APPLY_GATES:
        raise OperationError("input.invalid", f"Unsupported review apply gate: {apply_gate}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="review.update",
        requested_capabilities=["review.read_state"],
    )
    review_state = require_fixture_capability(fixture, "review.read_state")["result"]
    review = next((item for item in review_state.get("reviews", []) if item["id"] == review_id), None)
    if review is None:
        raise OperationError("review.not_found", f"Review not found: {review_id}")

    manifest_entry = manifest_operation("review.update")
    target_gate = apply_gate
    if target_gate is None and kind == "approval":
        target_gate = "approved"
    elif target_gate is None and kind == "blocker":
        target_gate = "blocked"

    review_result = {
        "id": review_id,
        "ref_policy": "opaque_ref",
        "current_status": review["status"],
        "current_apply_gate": review["apply_gate"],
        "update_kind": kind,
    }
    if target_gate is not None:
        review_result["target_apply_gate"] = target_gate

    return {
        "operation": {
            "name": manifest_entry["name"],
            "version": manifest_entry["version"],
            "stability": manifest_entry["stability"],
        },
        "mode": mode,
        "status": "requires_approval",
        "mutates": False,
        "review": review_result,
        "approval": {
            "required": True,
            "classes": manifest_entry["approval"]["classes"],
            "reason": "Review updates require approval before local review state is written.",
        },
        "side_effects": manifest_entry["side_effects"],
        "adapter_capabilities": manifest_entry["adapter_capabilities"],
        "preview": [
            {
                "kind": "filesystem.write",
                "path_policy": "category_only",
                "summary": f"Record {kind} update for the review session after gates pass.",
            }
        ],
        "verification": [
            {
                "kind": "approval_gate",
                "description": "Require local approval before writing review state.",
            },
            {
                "kind": "schema",
                "description": "Validate review update result shape before execution handoff.",
            },
        ],
        "warnings": [
            "This preview does not write review state.",
            "Apply-mode execution is blocked until write-capable review adapters and approval gates are exercised.",
        ],
        "reason": reason or "No local reason supplied.",
    }


def heartbeat_packet(
    detail: str = "summary",
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if detail not in {"summary", "full"}:
        raise OperationError("input.invalid", f"Unsupported heartbeat detail level: {detail}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="heartbeat.packet",
        requested_capabilities=[
            "project.resolve",
            "filesystem.read_project_metadata",
            "git.inspect_status",
            "incident.read_state",
            "review.read_state",
            "heartbeat.read_state",
        ],
    )
    project = require_fixture_capability(fixture, "project.resolve")["result"]
    metadata = require_fixture_capability(fixture, "filesystem.read_project_metadata")["result"]
    git_status = require_fixture_capability(fixture, "git.inspect_status")["result"]
    incident_state = require_fixture_capability(fixture, "incident.read_state")["result"]
    review_state = require_fixture_capability(fixture, "review.read_state")["result"]
    heartbeat_state = require_fixture_capability(fixture, "heartbeat.read_state")["result"]

    incidents = incident_state.get("incidents", [])
    reviews = review_state.get("reviews", [])
    stale_incidents = [incident for incident in incidents if incident["status"] == "stale" or incident.get("resurface")]
    blocked_reviews = [review for review in reviews if review["status"] == "blocked" or review["apply_gate"] == "blocked"]
    dirty = bool(git_status["repo"].get("dirty"))
    visible_progress_due = bool(heartbeat_state.get("visible_progress_due"))

    sections = [
        {
            "kind": "project",
            "status": "ok" if project.get("project_ref") else "blocked",
            "summary": f"{metadata['project']['name']} project metadata is readable.",
            "count": 1,
        },
        {
            "kind": "repository",
            "status": "attention" if dirty else "ok",
            "summary": "Repository has uncommitted changes." if dirty else "Repository status is clean in adapter state.",
            "count": git_status.get("worktree", {}).get("changed_count", 0),
        },
        {
            "kind": "incident",
            "status": "attention" if stale_incidents else "ok",
            "summary": f"{len(stale_incidents)} incident(s) need resurfacing.",
            "count": len(stale_incidents),
        },
        {
            "kind": "review",
            "status": "blocked" if blocked_reviews else "ok",
            "summary": f"{len(blocked_reviews)} review session(s) are blocked.",
            "count": len(blocked_reviews),
        },
        {
            "kind": "heartbeat",
            "status": "attention" if visible_progress_due else "ok",
            "summary": "Visible progress heartbeat is due." if visible_progress_due else "No visible heartbeat is due.",
            "count": heartbeat_state.get("due_count", 0),
        },
    ]
    if detail == "summary":
        sections = [section for section in sections if section["status"] != "ok"] or sections[:2]

    statuses = {section["status"] for section in sections}
    if "blocked" in statuses:
        overall_status = "blocked"
    elif "attention" in statuses:
        overall_status = "attention"
    else:
        overall_status = "ok"

    next_actions = {
        "ok": ["Continue with the next provider-boundary backlog item."],
        "attention": ["Review attention sections before claiming queues are clear."],
        "blocked": ["Resolve blocked sections before continuing autonomous work."],
    }[overall_status]

    generated_at = heartbeat_state.get("generated_at", "1970-01-01T00:00:00Z")
    return {
        "packet_id": f"heartbeat:{project.get('project_ref', 'unknown')}:{generated_at}",
        "generated_at": generated_at,
        "overall_status": overall_status,
        "sections": sections,
        "next_actions": next_actions,
    }


def heartbeat_check(
    scope: str = "all",
    detail: str = "summary",
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if scope not in {"project", "incident", "review", "all"}:
        raise OperationError("input.invalid", f"Unsupported heartbeat check scope: {scope}")
    if detail not in {"summary", "full"}:
        raise OperationError("input.invalid", f"Unsupported heartbeat check detail level: {detail}")

    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name="heartbeat.check",
        requested_capabilities=["heartbeat.read_state"],
    )
    heartbeat_state = require_fixture_capability(fixture, "heartbeat.read_state")["result"]
    due = bool(heartbeat_state.get("visible_progress_due"))
    due_count = heartbeat_state.get("due_count", 0)
    status = "due" if due else "not_due"
    summary = "Visible progress heartbeat is due." if due else "No visible heartbeat is due."

    checks = [
        {
            "kind": "heartbeat",
            "status": "attention" if due else "ok",
            "summary": summary,
        }
    ]
    if detail == "full":
        checks.append(
            {
                "kind": "project",
                "status": "ok",
                "summary": f"Heartbeat scope {scope!r} evaluated with {due_count} due item(s).",
            }
        )

    return {
        "due": due,
        "status": status,
        "reason": (
            f"{due_count} visible heartbeat item(s) are due."
            if due
            else "No visible heartbeat is due in synthetic heartbeat state."
        ),
        "checks": checks,
    }


def lifecycle_preview_steps(action: str) -> list[dict[str, str]]:
    summaries = {
        "bootstrap": [
            ("filesystem.write", "Create project skeleton and lifecycle files."),
            ("git.write", "Prepare branch and commit for the new project skeleton."),
        ],
        "adopt": [
            ("filesystem.read", "Inspect existing project metadata."),
            ("filesystem.write", "Bind project lifecycle metadata to the existing project."),
            ("git.write", "Prepare branch and commit for adoption metadata."),
        ],
        "repair": [
            ("filesystem.read", "Inspect missing or inconsistent lifecycle metadata."),
            ("filesystem.write", "Repair lifecycle files without changing unrelated project content."),
            ("git.write", "Prepare branch and commit for repair metadata."),
        ],
        "migrate": [
            ("filesystem.read", "Inspect current lifecycle layout."),
            ("filesystem.write", "Plan lifecycle layout or naming migration."),
            ("git.write", "Prepare branch and commit for migration metadata."),
        ],
        "archive": [
            ("filesystem.write", "Mark the project archived without deleting data."),
            ("git.write", "Prepare branch and commit for archive metadata."),
        ],
    }
    return [
        {
            "kind": kind,
            "path_policy": "category_only",
            "summary": summary,
        }
        for kind, summary in summaries[action]
    ]


def project_lifecycle_preview(operation_name: str, project_name: str, reason: str | None = None) -> dict[str, Any]:
    action = operation_name.removeprefix("project.")
    if action not in LIFECYCLE_ACTIONS:
        raise OperationError("catalog.command_not_found", f"Unsupported lifecycle operation: {operation_name}")
    manifest_entry = manifest_operation(operation_name)
    return {
        "operation": {
            "name": manifest_entry["name"],
            "version": manifest_entry["version"],
            "stability": manifest_entry["stability"],
        },
        "mode": "plan",
        "status": "requires_approval",
        "mutates": False,
        "project": {
            "name": project_name,
            "ref_policy": "opaque_ref",
        },
        "approval": {
            "required": True,
            "classes": manifest_entry["approval"]["classes"],
            "reason": "Lifecycle operations require approval before filesystem or git mutation.",
        },
        "side_effects": manifest_entry["side_effects"],
        "adapter_capabilities": manifest_entry["adapter_capabilities"],
        "preview": lifecycle_preview_steps(action),
        "verification": [
            {
                "kind": "operation_plan",
                "description": f"Generate and review an operation plan for {operation_name}.",
            },
            {
                "kind": "approval_gate",
                "description": "Require local approval before write-capable adapter execution.",
            },
            {
                "kind": "schema",
                "description": "Validate lifecycle result shape before execution handoff.",
            },
        ],
        "warnings": [
            "This preview does not perform filesystem or git mutations.",
            "Apply-mode execution is blocked until write-capable local adapters and approval gates exist.",
        ],
        "reason": reason or "No local reason supplied.",
    }


def lifecycle_blocked_result(
    manifest_entry: dict[str, Any],
    project_name: str,
    status: str,
    warnings: list[str],
    reason: str | None,
) -> dict[str, Any]:
    action = manifest_entry["name"].removeprefix("project.")
    return {
        "operation": {
            "name": manifest_entry["name"],
            "version": manifest_entry["version"],
            "stability": manifest_entry["stability"],
        },
        "mode": "apply",
        "status": status,
        "mutates": False,
        "project": {
            "name": project_name,
            "ref_policy": "opaque_ref",
        },
        "approval": {
            "required": True,
            "classes": manifest_entry["approval"]["classes"],
            "reason": "Lifecycle apply mode requires completed repo-mutation approval scoped to the operation plan.",
        },
        "side_effects": manifest_entry["side_effects"],
        "adapter_capabilities": manifest_entry["adapter_capabilities"],
        "preview": lifecycle_preview_steps(action),
        "verification": [
            {
                "kind": "approval_gate",
                "description": "Apply mode stopped before adapter write execution.",
            },
            {
                "kind": "schema",
                "description": "Validate blocked lifecycle apply result shape.",
            },
        ],
        "warnings": warnings,
        "reason": reason or "No local reason supplied.",
    }


def project_lifecycle_apply(
    operation_name: str,
    project_name: str,
    reason: str | None = None,
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    action = operation_name.removeprefix("project.")
    if action not in LIFECYCLE_ACTIONS:
        raise OperationError("catalog.command_not_found", f"Unsupported lifecycle operation: {operation_name}")
    manifest_entry = manifest_operation(operation_name)
    fixture = load_adapter(
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
        operation_name=operation_name,
        requested_capabilities=list(LIFECYCLE_APPLY_CAPABILITIES),
    )

    missing = [capability for capability in LIFECYCLE_APPLY_CAPABILITIES if capability not in fixture]
    if missing:
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "blocked",
            [f"Adapter fixture is missing apply capability {capability}." for capability in missing],
            reason,
        )

    project = require_fixture_capability(fixture, "project.resolve")["result"]
    git_status = require_fixture_capability(fixture, "git.inspect_status")["result"]
    approval = require_fixture_capability(fixture, "approval.request")["result"]

    if project.get("project_name") and project["project_name"] != project_name:
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "blocked",
            ["Adapter project reference does not match requested project name."],
            reason,
        )

    repo = git_status.get("repo", {})
    worktree = git_status.get("worktree", {})
    if repo.get("dirty") or int(worktree.get("changed_count", 0)) or int(worktree.get("untracked_count", 0)):
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "blocked",
            ["Git worktree is dirty in adapter state; lifecycle apply refused before write execution."],
            reason,
        )

    if not approval.get("approved"):
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "requires_approval",
            ["Repo-mutation approval is missing or incomplete."],
            reason,
        )
    if approval.get("approval_class") != "repo_mutation":
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "requires_approval",
            ["Approval class is not scoped to repo_mutation."],
            reason,
        )
    if approval.get("operation") != operation_name:
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "blocked",
            ["Approval is scoped to a different lifecycle operation."],
            reason,
        )
    if not approval.get("preview_reviewed"):
        return lifecycle_blocked_result(
            manifest_entry,
            project_name,
            "requires_approval",
            ["Lifecycle preview has not been marked reviewed by the local approval gate."],
            reason,
        )

    filesystem_write = require_fixture_capability(fixture, "filesystem.write_project_files")["result"]
    git_write = require_fixture_capability(fixture, "git.write_branch")["result"]
    filesystem_receipt = filesystem_write.get("receipt", {})
    git_receipt = git_write.get("receipt", {})
    post_write = (
        filesystem_receipt.get("verification", filesystem_write.get("verification", []))
        + git_receipt.get("verification", git_write.get("verification", []))
    )

    return {
        "operation": {
            "name": manifest_entry["name"],
            "version": manifest_entry["version"],
            "stability": manifest_entry["stability"],
        },
        "mode": "apply",
        "status": "applied",
        "mutates": True,
        "project": {
            "name": project_name,
            "ref_policy": "opaque_ref",
        },
        "approval": {
            "required": True,
            "classes": manifest_entry["approval"]["classes"],
            "reason": "Local adapter reported completed repo-mutation approval before write execution.",
        },
        "side_effects": manifest_entry["side_effects"],
        "adapter_capabilities": manifest_entry["adapter_capabilities"],
        "preview": lifecycle_preview_steps(action),
        "verification": [
            {
                "kind": "operation_plan",
                "description": "Operation plan was reviewed before apply-mode execution.",
            },
            {
                "kind": "approval_gate",
                "description": "Repo-mutation approval completed for this lifecycle operation.",
            },
            {
                "kind": "filesystem.write",
                "description": filesystem_receipt.get(
                    "summary",
                    filesystem_write.get("summary", "Adapter reported filesystem write completion."),
                ),
            },
            {
                "kind": "git.write",
                "description": git_receipt.get("summary", git_write.get("summary", "Adapter reported git write completion.")),
            },
            *[
                {
                    "kind": item.get("kind", "post_write"),
                    "description": item.get("summary", "Adapter reported post-write verification."),
                }
                for item in post_write
            ],
        ],
        "warnings": [],
        "reason": reason or "No local reason supplied.",
    }


def project_lifecycle(
    operation_name: str,
    project_name: str,
    mode: str = "plan",
    reason: str | None = None,
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> dict[str, Any]:
    if mode not in {"plan", "apply"}:
        raise OperationError("input.invalid", f"Unsupported lifecycle mode: {mode}")
    if mode == "plan":
        return project_lifecycle_preview(operation_name, project_name, reason=reason)
    return project_lifecycle_apply(
        operation_name,
        project_name,
        reason=reason,
        adapter_fixture_path=adapter_fixture_path,
        adapter_config_path=adapter_config_path,
    )

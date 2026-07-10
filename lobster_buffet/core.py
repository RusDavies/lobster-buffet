from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_FIXTURE = "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json"
ADAPTER_CONFIG_ENV = "LOBSTER_BUFFET_ADAPTER_CONFIG"
LIFECYCLE_ACTIONS = ("bootstrap", "adopt", "repair", "migrate", "archive")


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
    if config.get("backend", {}).get("kind") != "fixture":
        raise OperationError("adapter.config_invalid", "Only fixture-backed adapter config is implemented.")
    fixture_path = config["backend"].get("fixture_path")
    if not fixture_path:
        raise OperationError("adapter.config_invalid", "Adapter config is missing backend.fixture_path.")
    return {
        "fixture_path": resolve_path(fixture_path, path.parent),
    }


def resolve_adapter_fixture_path(
    adapter_fixture_path: Path | None = None,
    adapter_config_path: Path | None = None,
) -> Path:
    if adapter_fixture_path is not None:
        return resolve_path(adapter_fixture_path)

    config_path = adapter_config_path or default_adapter_config_path()
    if config_path is not None:
        config = load_adapter_config(resolve_path(config_path))
        return config["fixture_path"]

    return resolve_path(DEFAULT_ADAPTER_FIXTURE)


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
    fixture = load_adapter_fixture(
        resolve_adapter_fixture_path(adapter_fixture_path=adapter_fixture_path, adapter_config_path=adapter_config_path)
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

    fixture = load_adapter_fixture(
        resolve_adapter_fixture_path(adapter_fixture_path=adapter_fixture_path, adapter_config_path=adapter_config_path)
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

    fixture = load_adapter_fixture(
        resolve_adapter_fixture_path(adapter_fixture_path=adapter_fixture_path, adapter_config_path=adapter_config_path)
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

    fixture = load_adapter_fixture(
        resolve_adapter_fixture_path(adapter_fixture_path=adapter_fixture_path, adapter_config_path=adapter_config_path)
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

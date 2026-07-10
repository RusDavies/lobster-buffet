from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


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


def require_fixture_capability(fixture: dict[str, Any], capability: str) -> dict[str, Any]:
    envelope = fixture.get(capability)
    if envelope is None:
        raise OperationError("adapter.capability_missing", f"Adapter fixture is missing {capability}")
    if not envelope["ok"]:
        raise OperationError("adapter.capability_failed", f"Adapter fixture capability failed: {capability}")
    return envelope


def project_inspect(adapter_fixture_path: Path) -> dict[str, Any]:
    fixture = load_adapter_fixture(adapter_fixture_path)
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

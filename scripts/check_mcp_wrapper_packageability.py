#!/usr/bin/env python3
"""Validate MCP wrapper promotion status against packageability gates."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROMOTION_GATES = ROOT / "manifests/mcp-wrapper-promotion-gates.v0.1.0.json"
RELEASE_COMPATIBILITY = ROOT / "manifests/release-compatibility.v0.1.0.json"
DISTRIBUTION_HANDOFF = ROOT / "manifests/distribution-handoff.v0.1.0.json"

VALID_STATUSES = ("skeleton", "validated_skeleton", "packageable")
PRIVATE_FRAGMENTS = ("channel:", "/home/", "github.com/RusDavies")
EXPECTED_VALIDATION_REFS = {
    "scripts/check_initial_operation_schemas.py",
    "node wrappers/mcp/test.js",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def existing_ref(ref: str) -> bool:
    path_part = ref.split("#", 1)[0]
    if not path_part or path_part.startswith(("node ", "python3 ", "cd ")):
        return True
    return (ROOT / path_part).exists()


def command_validation_refs(validation_refs: list[str]) -> set[str]:
    return {ref for ref in validation_refs if ref.startswith(("node ", "python3 ", "cd "))}


def validate_common(
    gates: dict[str, Any],
    wrapper: dict[str, Any],
    package_json: dict[str, Any],
    release_compatibility: dict[str, Any],
    distribution_handoff: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if gates["current_status"] not in VALID_STATUSES:
        errors.append(f"promotion gates current_status must be one of {VALID_STATUSES}")
    if wrapper["status"] != gates["current_status"]:
        errors.append(
            "MCP wrapper status mismatch: "
            f"metadata has {wrapper['status']!r}, promotion gates have {gates['current_status']!r}"
        )
    if wrapper["provider_api"] != "lobster-buffet.provider.v0":
        errors.append("MCP wrapper metadata must declare provider API lobster-buffet.provider.v0")
    if wrapper["local_adapter_api"] != "lobster-buffet.local-adapter.v0":
        errors.append("MCP wrapper metadata must declare local adapter API lobster-buffet.local-adapter.v0")
    if wrapper["entrypoint"] != "wrappers/mcp/index.js":
        errors.append("MCP wrapper metadata must name wrappers/mcp/index.js as the entrypoint")
    if wrapper.get("server_entrypoint") != "wrappers/mcp/server.js":
        errors.append("MCP wrapper metadata must name wrappers/mcp/server.js as the server entrypoint")
    elif not (ROOT / wrapper["server_entrypoint"]).exists():
        errors.append("MCP wrapper metadata server entrypoint does not exist")
    if wrapper["delegates_to"] != "python3 -m lobster_buffet.cli":
        errors.append("MCP wrapper metadata must delegate to python3 -m lobster_buffet.cli")

    private_data = wrapper.get("private_data", {})
    if private_data.get("contains_private_values") is not False:
        errors.append("MCP wrapper metadata private_data.contains_private_values must be false")
    if private_data.get("private_refs_only") is not True:
        errors.append("MCP wrapper metadata private_data.private_refs_only must be true")

    tools = wrapper.get("tools", [])
    if not tools:
        errors.append("MCP wrapper metadata must declare at least one supported tool")
    for tool in tools:
        delegates_to = tool.get("delegates_to", [])
        if delegates_to[:3] != ["python3", "-m", "lobster_buffet.cli"]:
            errors.append(f"MCP wrapper tool {tool.get('name', '<unknown>')}: must delegate to CLI core")
        if tool.get("read_only") is False:
            if tool.get("apply_supported") is not True:
                errors.append(f"MCP wrapper mutating tool {tool['name']}: apply_supported must be true")
            if set(tool.get("modes", [])) != {"plan", "apply"}:
                errors.append(f"MCP wrapper mutating tool {tool['name']}: modes must be plan and apply")
            if tool.get("adapter_config_supported") is not True:
                errors.append(f"MCP wrapper mutating tool {tool['name']}: adapter config support is required")

    required_package_fields = ("name", "version", "description", "main", "scripts")
    for field in required_package_fields:
        if field not in package_json:
            errors.append(f"wrappers/mcp/package.json missing required field {field!r}")
    if package_json.get("main") != "index.js":
        errors.append("wrappers/mcp/package.json main must be index.js")
    if package_json.get("bin", {}).get("lobster-buffet-mcp") != "server.js":
        errors.append("wrappers/mcp/package.json must expose the lobster-buffet-mcp server bin")
    if package_json.get("scripts", {}).get("test") != "node test.js":
        errors.append("wrappers/mcp/package.json scripts.test must run node test.js")
    version = package_json.get("version", "")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("wrappers/mcp/package.json version must be a stable semver triplet")

    gate_ids = [gate["id"] for gate in gates["gates"]]
    if len(gate_ids) != len(set(gate_ids)):
        errors.append("MCP wrapper promotion gates contain duplicate gate ids")
    if len(gate_ids) < 10:
        errors.append("MCP wrapper promotion gates must cover the ten promotion criteria")
    validation_refs = {ref for gate in gates["gates"] for ref in gate["validation_refs"]}
    if not EXPECTED_VALIDATION_REFS.issubset(validation_refs):
        errors.append("MCP wrapper promotion gates must include schema and wrapper regression validation refs")
    if not command_validation_refs(sorted(validation_refs)):
        errors.append("MCP wrapper promotion gates must include executable validation commands")

    for ref in gates["wrapper"].values():
        if not existing_ref(ref):
            errors.append(f"MCP wrapper promotion gates: missing wrapper ref {ref}")
    for gate in gates["gates"]:
        if gate["packageable_required"] is not True:
            errors.append(f"MCP wrapper promotion gate {gate['id']}: packageable_required must be true")
        for ref in gate["evidence_refs"] + gate["validation_refs"]:
            if not existing_ref(ref):
                errors.append(f"MCP wrapper promotion gate {gate['id']}: missing ref {ref}")

    if "mcp_wrapper_promotion_gate_validation_passes" not in release_compatibility["release_gates"]:
        errors.append("release compatibility gates must include MCP wrapper promotion validation")

    handoff_paths = {item["path"] for item in distribution_handoff["packageable_artifacts"]}
    if "wrappers/mcp/" not in handoff_paths:
        errors.append("distribution handoff packageable artifacts must include wrappers/mcp/")
    if "manifests/mcp-wrapper-promotion-gates.v0.1.0.json" not in handoff_paths:
        errors.append("distribution handoff packageable artifacts must include MCP promotion gates")

    shared_text = (
        PROMOTION_GATES.read_text(encoding="utf-8")
        + (ROOT / gates["wrapper"]["metadata_ref"]).read_text(encoding="utf-8")
        + (ROOT / gates["wrapper"]["package_ref"]).read_text(encoding="utf-8")
    )
    for fragment in PRIVATE_FRAGMENTS:
        if fragment in shared_text:
            errors.append(f"MCP wrapper shared metadata contains forbidden private/local fragment {fragment!r}")

    return errors


def validate_declared_status(
    gates: dict[str, Any],
    wrapper: dict[str, Any],
    distribution_handoff: dict[str, Any],
) -> list[str]:
    status = gates["current_status"]
    errors: list[str] = []

    if status == "skeleton":
        return errors

    tool_operations = {tool["operation"] for tool in wrapper.get("tools", [])}
    if {"command.list", "project.inspect", "project.<lifecycle_action>"} - tool_operations:
        errors.append("validated_skeleton status requires command.list, project.inspect, and lifecycle tools")

    if status == "validated_skeleton":
        return errors

    if status == "packageable":
        if wrapper["status"] != "packageable":
            errors.append("packageable promotion requires wrapper metadata status packageable")
        packageable_paths = {item["path"] for item in distribution_handoff["packageable_artifacts"]}
        if not {"wrappers/mcp/", "manifests/mcp-wrapper-promotion-gates.v0.1.0.json"}.issubset(
            packageable_paths
        ):
            errors.append("packageable promotion requires wrapper and promotion gates in handoff metadata")
        return errors

    errors.append(f"unknown MCP wrapper promotion status {status!r}")
    return errors


def main() -> int:
    gates = load_json(PROMOTION_GATES)
    wrapper = load_json(ROOT / gates["wrapper"]["metadata_ref"])
    package_json = load_json(ROOT / gates["wrapper"]["package_ref"])
    release_compatibility = load_json(RELEASE_COMPATIBILITY)
    distribution_handoff = load_json(DISTRIBUTION_HANDOFF)

    errors = validate_common(gates, wrapper, package_json, release_compatibility, distribution_handoff)
    errors.extend(validate_declared_status(gates, wrapper, distribution_handoff))

    if errors:
        print("\n".join(errors))
        return 1

    print(
        "Validated MCP wrapper packageability status "
        f"{gates['current_status']} with {len(gates['gates'])} promotion gate(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the initial operation JSON schemas against checked-in fixtures.

This intentionally implements only the JSON Schema subset used by the first
schema slice so the repository does not need a validator dependency yet.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CHECKS = [
    (
        ROOT / "schemas/provider-operation-manifest.v0.1.0.json",
        ROOT / "manifests/provider-operations.v0.1.0.json",
    ),
    (
        ROOT / "schemas/operation-catalog.v0.1.0.json",
        ROOT / "manifests/operation-catalog.v0.1.0.json",
    ),
    (
        ROOT / "schemas/local-adapter-capabilities.v0.1.0.json",
        ROOT / "manifests/local-adapter-capabilities.v0.1.0.json",
    ),
    (
        ROOT / "schemas/distribution-handoff.v0.1.0.json",
        ROOT / "manifests/distribution-handoff.v0.1.0.json",
    ),
    (
        ROOT / "schemas/local-adapter-fixture.v0.1.0.json",
        ROOT / "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json",
    ),
    (
        ROOT / "schemas/local-adapter-config.v0.1.0.json",
        ROOT / "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json",
    ),
    (
        ROOT / "schemas/operation-plan.v0.1.0.json",
        ROOT / "fixtures/operations/operation.plan.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/command.describe.input.v0.1.0.json",
        ROOT / "fixtures/operations/command.describe.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/command.describe.output.v0.1.0.json",
        ROOT / "fixtures/operations/command.describe.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/project.inspect.input.v0.1.0.json",
        ROOT / "fixtures/operations/project.inspect.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/project.inspect.output.v0.1.0.json",
        ROOT / "fixtures/operations/project.inspect.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/project.lifecycle.input.v0.1.0.json",
        ROOT / "fixtures/operations/project.lifecycle.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/project.lifecycle.output.v0.1.0.json",
        ROOT / "fixtures/operations/project.lifecycle.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/command.list.input.v0.1.0.json",
        ROOT / "fixtures/operations/command.list.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/command.list.output.v0.1.0.json",
        ROOT / "fixtures/operations/command.list.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/git.workflow.inspect.input.v0.1.0.json",
        ROOT / "fixtures/operations/git.workflow.inspect.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/git.workflow.inspect.output.v0.1.0.json",
        ROOT / "fixtures/operations/git.workflow.inspect.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/alignment.scan.input.v0.1.0.json",
        ROOT / "fixtures/operations/alignment.scan.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/alignment.scan.output.v0.1.0.json",
        ROOT / "fixtures/operations/alignment.scan.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/incident.list.input.v0.1.0.json",
        ROOT / "fixtures/operations/incident.list.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/incident.list.output.v0.1.0.json",
        ROOT / "fixtures/operations/incident.list.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/incident.update.input.v0.1.0.json",
        ROOT / "fixtures/operations/incident.update.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/incident.update.output.v0.1.0.json",
        ROOT / "fixtures/operations/incident.update.output.valid.json",
    ),
    (
        ROOT / "schemas/operations/incident.close.input.v0.1.0.json",
        ROOT / "fixtures/operations/incident.close.input.valid.json",
    ),
    (
        ROOT / "schemas/operations/incident.close.output.v0.1.0.json",
        ROOT / "fixtures/operations/incident.close.output.valid.json",
    ),
]

MANIFEST = ROOT / "manifests/provider-operations.v0.1.0.json"
CATALOG = ROOT / "manifests/operation-catalog.v0.1.0.json"
ADAPTER_CAPABILITIES = ROOT / "manifests/local-adapter-capabilities.v0.1.0.json"
DISTRIBUTION_HANDOFF = ROOT / "manifests/distribution-handoff.v0.1.0.json"
ADAPTER_FIXTURE = ROOT / "fixtures/adapters/synthetic-project-inspect-adapter.v0.1.0.json"
ADAPTER_CONFIG = ROOT / "fixtures/adapters/synthetic-local-adapter-config.v0.1.0.json"


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def type_matches(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def validate(schema: dict[str, Any], value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not type_matches(expected_type, value):
        return [f"{path}: expected {expected_type}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']!r}")

    if isinstance(value, str) and "minLength" in schema:
        if len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than {schema['minLength']}")

    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema:
        if value < schema["minimum"]:
            errors.append(f"{path}: integer below minimum {schema['minimum']}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            for key in extra:
                errors.append(f"{path}: additional property {key!r} is not allowed")

        for key, child in value.items():
            if key in properties:
                errors.extend(validate(properties[key], child, f"{path}.{key}"))

    if isinstance(value, list) and "items" in schema:
        item_schema = schema["items"]
        for index, item in enumerate(value):
            errors.extend(validate(item_schema, item, f"{path}[{index}]"))

    return errors


def main() -> int:
    all_errors: list[str] = []
    for schema_path, fixture_path in CHECKS:
        schema = load_json(schema_path)
        fixture = load_json(fixture_path)
        errors = validate(schema, fixture)
        if errors:
            all_errors.append(f"{fixture_path.relative_to(ROOT)} failed {schema_path.relative_to(ROOT)}")
            all_errors.extend(f"  {error}" for error in errors)

    manifest = load_json(MANIFEST)
    catalog = load_json(CATALOG)
    adapter_capabilities = load_json(ADAPTER_CAPABILITIES)
    distribution_handoff = load_json(DISTRIBUTION_HANDOFF)
    adapter_fixture = load_json(ADAPTER_FIXTURE)
    adapter_config = load_json(ADAPTER_CONFIG)
    for operation in manifest["operations"]:
        for key in ("input_schema_ref", "output_schema_ref"):
            ref = ROOT / operation[key]
            if not ref.exists():
                all_errors.append(f"{operation['name']}: missing {key} {operation[key]}")

        definition_path = operation["definition_ref"].split("#", 1)[0]
        if not (ROOT / definition_path).exists():
            all_errors.append(f"{operation['name']}: missing definition {operation['definition_ref']}")

        if not operation["read_only"] and not operation["approval"]["required"]:
            all_errors.append(f"{operation['name']}: mutating operations must require approval")

    operation_names = [operation["name"] for operation in catalog["operations"]]
    if len(operation_names) != len(set(operation_names)):
        all_errors.append("operation catalog contains duplicate operation names")

    schema_defined = {operation["name"] for operation in manifest["operations"]}
    for name in schema_defined:
        if name not in operation_names:
            all_errors.append(f"{name}: schema-backed operation missing from operation catalog")

    for operation in catalog["operations"]:
        if operation["implementation_state"] == "schema_defined" and operation["name"] not in schema_defined:
            all_errors.append(f"{operation['name']}: marked schema_defined but missing from provider manifest")

    capability_names = [capability["name"] for capability in adapter_capabilities["capabilities"]]
    if len(capability_names) != len(set(capability_names)):
        all_errors.append("adapter capability catalog contains duplicate capability names")

    known_capabilities = set(capability_names)
    for source, operations in (
        ("provider manifest", manifest["operations"]),
        ("operation catalog", catalog["operations"]),
    ):
        for operation in operations:
            for capability in operation["adapter_capabilities"]:
                if capability not in known_capabilities:
                    all_errors.append(
                        f"{operation['name']}: {source} references undefined adapter capability {capability!r}"
                    )

    for section in ("packageable_artifacts", "inspectable_refs"):
        for item in distribution_handoff[section]:
            path = ROOT / item["path"]
            if not path.exists():
                all_errors.append(f"distribution handoff {section}: missing path {item['path']}")

    required_fixture_capabilities = {
        "project.resolve",
        "filesystem.read_project_metadata",
        "git.inspect_status",
        "incident.read_state",
    }
    fixture_capabilities = {item["name"]: item["envelope"] for item in adapter_fixture["capabilities"]}
    for capability in sorted(required_fixture_capabilities):
        envelope = fixture_capabilities.get(capability)
        if envelope is None:
            all_errors.append(f"adapter fixture missing capability {capability}")
            continue
        if envelope["capability"] != capability:
            all_errors.append(f"adapter fixture {capability}: envelope capability mismatch")
        if envelope["ok"] is not True:
            all_errors.append(f"adapter fixture {capability}: expected ok=true")
        private_data = envelope["private_data"]
        if private_data["contains_private_values"]:
            all_errors.append(f"adapter fixture {capability}: contains_private_values must be false")
        if not private_data["private_refs_only"]:
            all_errors.append(f"adapter fixture {capability}: private_refs_only must be true")

    fixture_ref = ADAPTER_CONFIG.parent / adapter_config["backend"]["fixture_path"]
    if not fixture_ref.exists():
        all_errors.append(f"adapter config references missing fixture {adapter_config['backend']['fixture_path']}")

    forbidden_fragments = ("channel:", "0000000000000000000", "/home/", "github.com/RusDavies")
    fixture_text = ADAPTER_FIXTURE.read_text(encoding="utf-8") + ADAPTER_CONFIG.read_text(encoding="utf-8")
    for fragment in forbidden_fragments:
        if fragment in fixture_text:
            all_errors.append(f"adapter fixture contains forbidden private/local fragment {fragment!r}")

    if all_errors:
        print("\n".join(all_errors))
        return 1

    print(
        f"Validated {len(CHECKS)} schema fixture(s), "
        f"{len(manifest['operations'])} manifest operation(s), "
        f"{len(catalog['operations'])} catalog operation(s), "
        f"{len(adapter_capabilities['capabilities'])} adapter capability(ies), "
        f"{len(distribution_handoff['packageable_artifacts'])} handoff artifact(s), "
        f"and {len(adapter_fixture['capabilities'])} adapter fixture capability(ies)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

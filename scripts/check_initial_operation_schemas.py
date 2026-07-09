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
]

MANIFEST = ROOT / "manifests/provider-operations.v0.1.0.json"
CATALOG = ROOT / "manifests/operation-catalog.v0.1.0.json"


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
    for operation in manifest["operations"]:
        for key in ("input_schema_ref", "output_schema_ref"):
            ref = ROOT / operation[key]
            if not ref.exists():
                all_errors.append(f"{operation['name']}: missing {key} {operation[key]}")

        definition_path = operation["definition_ref"].split("#", 1)[0]
        if not (ROOT / definition_path).exists():
            all_errors.append(f"{operation['name']}: missing definition {operation['definition_ref']}")

        if not operation["read_only"]:
            all_errors.append(f"{operation['name']}: initial operations must be read-only")

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

    if all_errors:
        print("\n".join(all_errors))
        return 1

    print(
        f"Validated {len(CHECKS)} schema fixture(s), "
        f"{len(manifest['operations'])} manifest operation(s), "
        f"and {len(catalog['operations'])} catalog operation(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

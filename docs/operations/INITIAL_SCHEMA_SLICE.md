# Initial Operation Schema Slice

## Scope

This slice defines the first two portable Lobster Buffet operations:

- `command.describe(name)`
- `project.inspect(context)`

The goal is to give Lobster Buffet, Lobster Portage, local adapters, and future Redshield integrations a concrete shared-provider target before choosing the final runtime transport.

## Schema Goals

- Describe operations in a versioned, machine-readable way.
- Keep private workspace data outside shared schemas.
- Declare side effects, approval gates, and error states before implementation.
- Provide enough package metadata for Lobster Portage manifest and doctor checks.
- Provide enough operation-plan metadata for future Redshield Warden and Redshield Armor review.

## Operation Identifier

Each operation should have a stable identifier:

```json
{
  "namespace": "lobster-buffet",
  "name": "command.describe",
  "version": "0.1.0",
  "stability": "draft"
}
```

Rules:

- `namespace` identifies the provider package.
- `name` is dot-separated and action-oriented.
- `version` is semantic and belongs to the operation contract, not the provider release.
- `stability` is one of `draft`, `experimental`, `stable`, or `deprecated`.

## Shared Operation Metadata

Every operation definition should include:

```json
{
  "id": {
    "namespace": "lobster-buffet",
    "name": "command.describe",
    "version": "0.1.0",
    "stability": "draft"
  },
  "summary": "Describe a known command and its execution contract.",
  "inputs_schema_ref": "schemas/operations/command.describe.input.v0.1.0.json",
  "outputs_schema_ref": "schemas/operations/command.describe.output.v0.1.0.json",
  "side_effects": [],
  "approval": {
    "required": false,
    "reason": "Read-only catalog lookup."
  },
  "adapter_capabilities": [],
  "errors": [
    "operation.unsupported",
    "input.invalid",
    "catalog.command_not_found"
  ]
}
```

## Side Effect Model

`side_effects` should be explicit and empty for read-only operations.

Allowed draft categories:

- `none`
- `filesystem.read`
- `filesystem.write`
- `git.read`
- `git.write`
- `network.read`
- `network.write`
- `message.visible_send`
- `external.action`
- `secret.read`

This slice uses `none`, `filesystem.read`, and `git.read` only.

## Approval Model

Operations must declare approval needs even when no approval is needed:

```json
{
  "required": false,
  "reason": "Read-only project inspection.",
  "classes": []
}
```

Draft approval classes:

- `external_action`
- `public_release`
- `destructive_change`
- `secret_access`
- `private_data_export`
- `repo_mutation`
- `visible_message_send`

## Error Model

Errors should be stable enough for LLM summarization and deterministic callers.

Common errors:

- `operation.unsupported`
- `operation.version_unsupported`
- `input.invalid`
- `adapter.capability_missing`
- `adapter.ambiguous_context`
- `adapter.private_data_blocked`
- `project.not_found`
- `project.not_git_repo`
- `catalog.command_not_found`

Each error result should include:

```json
{
  "code": "project.not_found",
  "message": "Project context could not be resolved.",
  "retryable": false,
  "details": {}
}
```

`details` must not include secrets, private channel IDs, personal memory, or unrelated local paths in shared output unless a local adapter explicitly allows that disclosure.

## Package Metadata For Lobster Portage

Lobster Portage should be able to inspect a provider package and answer:

- Which operation definitions are present?
- Which schema files are required?
- Which operations are read-only versus mutating?
- Which adapter capabilities are required?
- Which operation versions are supported?
- Which files are managed by the package and which are local-only?

Draft package manifest fields:

```json
{
  "package": "lobster-buffet",
  "provider_api": "lobster-buffet.provider.v0",
  "operations": [
    {
      "name": "command.describe",
      "version": "0.1.0",
      "definition": "docs/operations/INITIAL_SCHEMA_SLICE.md#commanddescribename",
      "read_only": true,
      "adapter_capabilities": []
    },
    {
      "name": "project.inspect",
      "version": "0.1.0",
      "definition": "docs/operations/INITIAL_SCHEMA_SLICE.md#projectinspectcontext",
      "read_only": true,
      "adapter_capabilities": [
        "project.resolve",
        "filesystem.read_project_metadata",
        "git.inspect_status"
      ]
    }
  ]
}
```

## `command.describe(name)`

### Purpose

Return a structured description of a known command or operation so an agent can explain usage, side effects, approval gates, and expected result shape without reading long prompt procedures.

### Input

```json
{
  "name": "project.inspect",
  "detail": "summary"
}
```

Fields:

- `name`: required operation or command name.
- `detail`: optional, one of `summary`, `schema`, or `full`; defaults to `summary`.

### Output

```json
{
  "operation": {
    "name": "project.inspect",
    "version": "0.1.0",
    "stability": "draft"
  },
  "summary": "Inspect project context and return structured local state.",
  "inputs": {
    "schema_ref": "schemas/operations/project.inspect.input.v0.1.0.json"
  },
  "outputs": {
    "schema_ref": "schemas/operations/project.inspect.output.v0.1.0.json"
  },
  "side_effects": [
    "filesystem.read",
    "git.read"
  ],
  "approval": {
    "required": false,
    "classes": []
  },
  "adapter_capabilities": [
    "project.resolve",
    "filesystem.read_project_metadata",
    "git.inspect_status"
  ],
  "errors": [
    "adapter.ambiguous_context",
    "project.not_found",
    "project.not_git_repo"
  ]
}
```

### Side Effects

- Read-only.
- No visible messages.
- No external network.
- No mutation.

### Approval

No approval required for catalog lookup.

### Errors

- `input.invalid`
- `catalog.command_not_found`
- `operation.version_unsupported`

## `project.inspect(context)`

### Purpose

Resolve a local project context and return compact structured state before any mutating project operation is attempted.

### Input

```json
{
  "context": {
    "source": "channel",
    "label": "#lobster-buffet"
  },
  "detail": "summary"
}
```

Fields:

- `context`: required local adapter context. Shared schemas describe its shape, but local adapters decide how to resolve private identifiers.
- `detail`: optional, one of `summary`, `status`, or `full`; defaults to `summary`.

### Output

```json
{
  "project": {
    "name": "lobster-buffet",
    "kind": "software",
    "lifecycle_state": "active",
    "privacy": "public-candidate"
  },
  "repo": {
    "is_git_repo": true,
    "branch": "main",
    "dirty": false,
    "ahead": 0,
    "behind": 0
  },
  "backlog": {
    "open_next": 7,
    "open_later": 8,
    "done": 1
  },
  "capabilities": {
    "can_read_files": true,
    "can_inspect_git": true,
    "can_mutate": false
  },
  "warnings": []
}
```

Output rules:

- Shared results should avoid raw private channel IDs, hostnames, personal memory, secrets, and unrelated local paths.
- Local adapters may include richer local detail only when the caller and surface are allowed to see it.
- `dirty`, `ahead`, and `behind` are informational; they do not authorize git mutation.

### Side Effects

- `filesystem.read`
- `git.read`

No writes, visible messages, external actions, or network access are required.

### Approval

No approval required for read-only inspection.

### Adapter Capabilities

- `project.resolve`
- `filesystem.read_project_metadata`
- `git.inspect_status`

### Errors

- `input.invalid`
- `adapter.capability_missing`
- `adapter.ambiguous_context`
- `adapter.private_data_blocked`
- `project.not_found`
- `project.not_git_repo`

## Operation Plan Metadata

Before execution, providers should be able to emit an operation plan:

```json
{
  "operation": {
    "name": "project.inspect",
    "version": "0.1.0"
  },
  "read_only": true,
  "side_effects": [
    "filesystem.read",
    "git.read"
  ],
  "approval": {
    "required": false,
    "classes": []
  },
  "adapter_capabilities": [
    "project.resolve",
    "filesystem.read_project_metadata",
    "git.inspect_status"
  ],
  "affected_surfaces": [
    "local_project",
    "local_git_repo"
  ],
  "expected_verification": [
    "schema_validate_output",
    "confirm_no_mutation"
  ]
}
```

Redshield Warden can review this plan for policy. Redshield Armor can review it for hardening, boundary, and conformance checks.

## Initial Validation Checklist

The first implementation should prove:

- `command.describe(name)` returns deterministic metadata for both initial operations.
- `command.describe(name)` fails cleanly for unknown commands.
- `project.inspect(context)` returns read-only project state through a local adapter.
- `project.inspect(context)` does not expose private adapter internals by default.
- both operations can emit operation plans before execution.
- Lobster Portage can discover operation names, versions, schema refs, side effects, and adapter capabilities from package metadata.

## Deferred Work

- Define a provider package manifest format with Lobster Portage.
- Define the audit event schema for Warden and Armor evidence.
- Decide the runtime transport after this schema slice has been reviewed.

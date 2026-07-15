# MCP Wrapper Compatibility Target

Status: Draft v0.1 target. This defines the wrapper compatibility target; it
does not implement an MCP server yet.

## Purpose

The MCP-style wrapper should expose the same Lobster Buffet operation surface as
the CLI core through a Model Context Protocol compatible tool transport.

It exists for broader tool/client compatibility. It must not become a second
operation implementation, a hosted service, or a place where local private state
is embedded in shared artifacts.

## Compatibility Identity

- Provider API: `lobster-buffet.provider.v0`
- Local adapter API: `lobster-buffet.local-adapter.v0`
- Target wrapper ref: `wrappers/mcp/`
- Skeleton metadata: `wrappers/mcp/mcp.wrapper.json`
- Promotion gate metadata: `manifests/mcp-wrapper-promotion-gates.v0.1.0.json`
- Compatibility target doc: `docs/operations/MCP_WRAPPER_COMPATIBILITY.md`

An MCP wrapper release must declare the provider API and local adapter API it
supports. Incompatible changes to operation names, required inputs, output
envelopes, side-effect metadata, approval metadata, or adapter capability names
must follow the release compatibility policy.

## Source Of Truth

The MCP wrapper must delegate to the same CLI core used by the OpenClaw dynamic
wrapper:

```bash
python3 -m lobster_buffet.cli ...
```

The wrapper may translate MCP tool parameters into CLI arguments, but it must
not reimplement operation behavior, local adapter loading, lifecycle gates,
approval checks, or command-backed adapter invocation.

## Tool Mapping

The wrapper should derive its tool surface from the schema-backed operation
catalog and provider manifest. Initial tool names should use the existing
OpenClaw wrapper naming pattern where practical:

- `lobster_buffet_command_list`
- `lobster_buffet_command_describe`
- `lobster_buffet_operation_plan`
- `lobster_buffet_project_inspect`
- `lobster_buffet_project_lifecycle`
- `lobster_buffet_git_workflow_guard`
- `lobster_buffet_incident_list`
- `lobster_buffet_alignment_scan`
- `lobster_buffet_review_list`
- `lobster_buffet_review_update`
- `lobster_buffet_heartbeat_packet`
- `lobster_buffet_heartbeat_check`

If a specific MCP SDK requires a stricter naming shape, the wrapper may adapt
names mechanically, but the mapping must be documented and deterministic.

## Inputs And Outputs

Inputs should be generated from, or kept in lockstep with, the corresponding
operation input schemas under `schemas/operations/`.

Outputs must preserve the CLI result JSON without dropping:

- operation name, version, and stability;
- mode, status, and mutation flags;
- side effects and adapter capabilities;
- approval and verification metadata;
- warnings and reasons;
- structured error envelopes.

MCP text output may include pretty JSON for human readability, but the full
machine-readable result must remain available to callers through the transport's
structured payload shape.

## Error Propagation

CLI JSON error envelopes must remain structured wrapper results. Adapter command
failures such as invalid JSON, nonzero exit, timeout, and missing capabilities
must not be flattened into generic transport exceptions.

The wrapper may use transport-level errors only when it cannot invoke the CLI or
cannot parse any CLI JSON output at all.

## Adapter Configuration

The MCP wrapper should support the same local adapter configuration model as
the CLI core and OpenClaw wrapper:

- explicit adapter fixture path for tests;
- explicit adapter config path for local deployments;
- `LOBSTER_BUFFET_ADAPTER_CONFIG` fallback where appropriate;
- local-only adapter config outside packageable shared artifacts.

Shared MCP wrapper metadata must not include Discord channel IDs, absolute local
paths, secrets, credentials, remotes, personal memory, or private runtime data.

## Compatibility Gates

Before an MCP wrapper is treated as packageable, it should have:

1. A wrapper metadata file declaring supported provider and adapter API versions.
2. A smoke test that proves at least `command.list` delegates to the CLI core.
3. A stateful operation test, initially `project.inspect`, using synthetic
   adapter config.
4. A mutating-operation preview/apply test that preserves lifecycle approval and
   mutation metadata.
5. A command failure propagation test that preserves CLI JSON error envelopes.
6. A local-only boundary check for wrapper metadata and synthetic outputs.

These gates should complement, not replace, existing CLI, schema, lifecycle,
and OpenClaw wrapper regression checks.
The machine-readable gate list lives in
`manifests/mcp-wrapper-promotion-gates.v0.1.0.json` and is validated by
`scripts/check_initial_operation_schemas.py`.

## Promotion Criteria

The MCP wrapper remains `skeleton` until all packageable-wrapper criteria below
are true in the same release candidate:

1. `wrappers/mcp/mcp.wrapper.json` declares `status: packageable` and names the
   exact provider API, local adapter API, entrypoint, delegated CLI command, and
   supported tool list.
2. `wrappers/mcp/package.json` has package metadata suitable for downstream
   packaging: stable name, version, description, entrypoint, test command, and
   no private local paths or runtime-only configuration.
3. The wrapper exposes every operation marked as supported in
   `mcp.wrapper.json`, and each supported tool delegates to the CLI core rather
   than reimplementing operation behavior.
4. Tool input schemas are either generated from operation schemas or reviewed
   against those schemas with drift called out in this document.
5. Structured MCP results preserve the CLI JSON payload, including errors,
   warnings, side effects, approval metadata, and mutation flags.
6. Apply-capable tools preserve preview-first behavior, approval checks,
   adapter capability checks, dirty-state blocks, stale-approval blocks, and
   post-write verification results.
7. Wrapper tests cover metadata, read-only delegation, stateful adapter-backed
   delegation, preview/apply lifecycle behavior, command failure propagation,
   unknown-tool errors, and local-only boundary fragments.
8. Release gates include `wrappers/mcp` regression checks alongside CLI,
   schema, lifecycle, command-adapter, and OpenClaw wrapper checks.
9. Distribution handoff metadata lists the wrapper as packageable and identifies
   any downstream packaging notes without moving Portage-owned package, doctor,
   install, rollback, or release mechanics into Buffet.
10. Local deployments can point the wrapper at an explicit adapter config or the
    `LOBSTER_BUFFET_ADAPTER_CONFIG` fallback without embedding private adapter
    data in shared metadata.

A release candidate that satisfies the test coverage but lacks package metadata
or handoff metadata should be treated as `validated_skeleton`, not packageable.
A release candidate that adds an SDK-specific MCP transport can be packageable
only if the transport layer stays thin and delegates to the same wrapper/core
path validated by `wrappers/mcp/test.js`.

## Current Skeleton

The current skeleton lives in `wrappers/mcp/`. It is SDK-neutral and exposes:

- `wrappers/mcp/mcp.wrapper.json` for provider API, adapter API, entrypoint, and
  initial tool metadata;
- `wrappers/mcp/index.js` for MCP-shaped tool listing and tool calls;
- `wrappers/mcp/test.js` for smoke tests proving `command.list`,
  `project.inspect`, lifecycle preview, blocked lifecycle apply paths, and the
  approved synthetic lifecycle apply path delegate to the CLI core while
  preserving CLI error envelopes for command-backed adapter failures.

The skeleton is not a complete MCP server yet. It is the compatibility and
delegation base for the next implementation slices. Current delegated tools:

- `lobster_buffet_command_list`
- `lobster_buffet_project_inspect`
- `lobster_buffet_project_lifecycle` preview mode and synthetic apply paths

## Non-Goals

- No hosted provider runtime.
- No direct reads of private workspace files by the wrapper.
- No wrapper-specific operation semantics.
- No bypass of local adapter approval or disclosure policy.
- No Portage-owned packaging logic inside the wrapper.

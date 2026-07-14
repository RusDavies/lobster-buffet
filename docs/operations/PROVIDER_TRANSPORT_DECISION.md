# Provider Transport Decision

Status: Accepted for v0.x.

## Decision

Lobster Buffet should use a layered provider transport:

1. CLI core as the canonical local execution layer.
2. OpenClaw dynamic tool provider wrapper as the first native integration.
3. MCP-style wrapper later, after the operation and adapter contracts are
   stable.

The CLI core owns deterministic operation execution, schema validation, fixture
tests, and local adapter loading. Wrappers should be thin transport adapters
around the same operation registry.

## Why This Shape

The project goal is portable OpenClaw process operations without copying private
workspace state or relying on long prompt procedures. A CLI-first core fits that
better than making a single provider runtime the source of truth:

- easy to test in public/open-source CI without OpenClaw runtime secrets;
- easy for Lobster Portage to package, version, and validate;
- easy for local instances to run with their own adapter config;
- easy to wrap as OpenClaw dynamic tools;
- possible to wrap as MCP later without reimplementing operation logic;
- less risk of accidentally creating a hosted service or runtime dependency.

## Rejected Alternatives

### OpenClaw Dynamic Tool Provider Only

This is attractive for first use inside OpenClaw, but it would make operation
logic harder to test and reuse outside one runtime surface. Dynamic tools should
be the first wrapper, not the core.

### MCP-Style Provider First

MCP may be useful for broader compatibility later, but starting there adds
transport design work before the operation catalog and adapter contract are
stable. Keep it as a wrapper target.

### Hosted Provider

Hosted operation execution is out of scope for v0.x. It would add privacy,
security, tenancy, uptime, billing, and support obligations that the product
brief explicitly avoids.

## Initial CLI Shape

Suggested command shape:

```bash
lobster-buffet operation describe --name project.inspect --format json
lobster-buffet operation inspect-project --context-json /path/to/context.json --format json
lobster-buffet operation plan --name project.inspect --context-json /path/to/context.json --format json
```

The exact command names can change during implementation, but the transport
contract should preserve:

- JSON input and output;
- schema-versioned operation results;
- explicit side effects and approval gates;
- local adapter capability errors;
- no raw private adapter state unless explicitly authorized locally;
- machine-readable errors suitable for LLM summarization.

## Adapter Loading

The CLI core should support local adapter configuration outside distributable
provider artifacts.

Adapters own:

- channel/session context;
- project root resolution;
- Git/GitHub provider configuration;
- visible-message surfaces;
- local approval policy;
- secrets and credentials.

Shared operation logic should consume adapter-provided scoped results, not read
private workspace files directly.

## Wrapper Responsibilities

### OpenClaw Dynamic Tool Wrapper

The first wrapper should expose a small subset of operations as OpenClaw dynamic
tools. It should:

- translate tool arguments into CLI/core operation calls;
- return compact structured results;
- preserve side-effect and approval metadata;
- rely on local adapter config supplied by the target instance.

### MCP Wrapper

An MCP-style wrapper can follow once the CLI core and adapter contracts are
stable. It should reuse the same operation registry and schemas.

The compatibility target is defined in
`docs/operations/MCP_WRAPPER_COMPATIBILITY.md`. Implementation should wait
until the target's delegation, naming, error propagation, adapter configuration,
and local-only boundaries are satisfied without creating wrapper-specific
operation semantics.

The initial skeleton lives in `wrappers/mcp/` and delegates `command.list` to
the CLI core as the first smoke-tested MCP-style tool surface.

## Redshield Integration

The CLI core should be able to produce operation plans before execution. Those
plans are the input to the Redshield Warden/Armor operation gate contract in
`docs/operations/REDSHIELD_OPERATION_GATE_CONTRACT.md`.

Redshield products remain optional and adjacent. The CLI core must remain useful
without paid policy or hardening products.

## Lobster Portage Integration

Lobster Portage should distribute or reference:

- CLI package metadata;
- operation schemas;
- provider operation manifests;
- fixtures;
- release and rollback notes;
- wrapper entrypoint metadata when wrappers are packaged.

Portage should not own runtime execution, local adapter config, or Redshield
runtime decisions.

## Test Plan

The first implementation slice should prove:

1. `command.describe` can run through the CLI core against fixture data.
2. `project.inspect` can run through the CLI core with a synthetic local
   adapter fixture.
3. operation results validate against JSON Schemas.
4. operation plans can be generated without exposing raw private adapter state.
5. the OpenClaw dynamic tool wrapper can call the same core without duplicating
   operation logic.

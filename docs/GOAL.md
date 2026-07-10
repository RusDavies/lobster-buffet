# Goal

Build a portable shared-provider layer for OpenClaw process operations.

The first useful version should define the operation catalog, local adapter
boundary, and CLI-core provider transport well enough that one high-value
operation can be implemented without copying private workspace data or relying
on long prompt procedures.

## Immediate Outcomes

- Use the accepted provider shape: CLI core with an OpenClaw dynamic tool
  wrapper first and MCP-style wrapper later.
- Define operation schemas for command catalog/help and project inspection.
- Define local adapter contracts for channel/project mapping, filesystem roots, git remotes, and visible-message surfaces.
- Identify how Lobster Portage should distribute or version the provider.
- Preserve public open-source suitability from the start.

## First Implementation Slice

Use the accepted CLI-core provider shape to prove two candidate operations:

1. `command.describe(name)`
2. `project.inspect(context)`

The implementation slice should produce executable CLI-core behavior, synthetic
adapter fixtures, schema validation, operation plans, privacy-safe results, and
a test path that wrapper transports can reuse without duplicating operation
logic.
